"""Main pipeline: orchestrates the hybrid parsing flow.
Stage 0: Clarify (Prism layout parsing) → Cleaned Markdown
Stage 1: Split + Merge (AI3Dstoryboard scene detection) → SceneRecords
Stage 1.5: Scan (spaCy NER pre-scan) → Global registry
Stage 2: Extract (characters, locations, visual elements)
Stage 3: Semantic (LLM routing for shots + scene intention/beat analysis)
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .schemas.scene import SceneRecord
from .schemas.character import GlobalCharacter, SceneCharacterInstance, SceneBackgroundPopulation
from .schemas.location import GlobalLocationAsset, SceneLocationInstance
from .schemas.visual_element import GlobalVisualElement, SceneVisualElement, ScenePropInteraction, CharacterEquipmentInstance
from .schemas.semantic import SceneIntentionAnalysis, SceneBeat
from .schemas.report import ParseReport, ReviewRecord, WarningRecord
from .input_adapters.text_reader import read_script_text
from .input_adapters.models import ScriptInput
from .clarifier.pdf_clarifier import pdf_clarify
from .clarifier.docx_clarifier import docx_clarify
from .scanner.nlp_engine import PrismNLPEngine
from .parser.scene_splitter import split_heading_blocks_from_md
from .parser.scene_merger import merge_heading_blocks
from .parser.character_extractor import extract_characters
from .parser.location_classifier import classify_locations, resolve_effective_periods
from .parser.visual_element_extractor import extract_visual_elements
from .parser.period_resolver import resolve_effective_periods as resolve_periods
from .validators.schema_validator import validate_records
from .llm.washer import ScriptWasher
from .exporters.output_package import export_output_package

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    scenes: list[SceneRecord] = field(default_factory=list)
    report: ParseReport | None = None
    global_characters: list[GlobalCharacter] = field(default_factory=list)
    scene_character_instances: list[SceneCharacterInstance] = field(default_factory=list)
    scene_background_populations: list[SceneBackgroundPopulation] = field(default_factory=list)
    global_location_assets: list[GlobalLocationAsset] = field(default_factory=list)
    scene_location_instances: list[SceneLocationInstance] = field(default_factory=list)
    global_visual_elements: list[GlobalVisualElement] = field(default_factory=list)
    scene_visual_elements: list[SceneVisualElement] = field(default_factory=list)
    character_equipment_instances: list[CharacterEquipmentInstance] = field(default_factory=list)
    scene_prop_interactions: list[ScenePropInteraction] = field(default_factory=list)
    scene_intention_analyses: list[SceneIntentionAnalysis] = field(default_factory=list)
    scene_beats: list[SceneBeat] = field(default_factory=list)
    reviews: list[ReviewRecord] = field(default_factory=list)
    extraction_warnings: list[WarningRecord] = field(default_factory=list)


def run_pipeline(
    script_path: str | Path,
    stage: int = 3,
    use_llm: bool = True,
    use_nlp: bool = True,
    use_wash: bool = False,
    output_dir: str | Path | None = None,
    progress: Callable[[str], None] | None = None,
    llm_cache_dir: str | Path | None = None,
) -> ParseResult:
    source_path = Path(script_path)
    _log(progress, f"[stage0] Reading input: {source_path}")
    suffix = source_path.suffix.lower()

    # Stage 0: Clarify
    if suffix in {".pdf"}:
        _log(progress, "[stage0] Running PDF clarifier (layout-aware)")
        md_text = pdf_clarify(str(source_path))
    elif suffix in {".docx"}:
        _log(progress, "[stage0] Running DOCX clarifier (layout-aware)")
        md_text = docx_clarify(str(source_path))
    else:
        _log(progress, "[stage0] Falling back to raw text reader")
        script_input = read_script_text(source_path)
        md_text = script_input.text

    # Stage 1: Split + Merge
    _log(progress, "[stage1] Detecting scene headings from clarified Markdown")
    blocks = split_heading_blocks_from_md(md_text)
    # Fallback: if no #-prefixed headings found, try raw heading detection
    if not blocks:
        from .parser.scene_heading_detector import detect_scene_headings_from_raw
        from .parser.scene_heading_parser import parse_scene_heading
        from .parser.scene_splitter import HeadingBlock
        raw_lines = md_text.splitlines(keepends=True)
        candidates = detect_scene_headings_from_raw(raw_lines)
        for idx, c in enumerate(candidates, start=1):
            from .utils.ids import heading_id
            heading = parse_scene_heading(c.raw, heading_id(idx))
            end = candidates[idx].line_index if idx < len(candidates) else len(raw_lines)
            blocks.append(HeadingBlock(heading=heading, start_line=c.line_index, end_line=end, original_text=''.join(raw_lines[c.line_index:end])))
    _log(progress, "[stage1] Creating scene records with shot timeline")
    scenes = merge_heading_blocks(blocks, source_path.name, md_text)
    _log(progress, f"[stage1] Created {len(scenes)} scenes, {sum(len(s.shots) for s in scenes)} shots")

    report = ParseReport(
        source_file=source_path.name,
        input_format=suffix.lstrip("."),
        stage=stage,
        heading_count=len(blocks),
        scene_count=len(scenes),
        shot_count=sum(len(s.shots) for s in scenes),
    )

    result = ParseResult(scenes=scenes, report=report)

    # Stage 1.5: NLP Pre-scan
    if stage >= 2 and use_nlp:
        _log(progress, "[stage1.5] NLP pre-scan with spaCy")
        try:
            nlp_engine = PrismNLPEngine()
            registry = nlp_engine.scan_and_register(md_text)
            _log(progress, f"[stage1.5] Found {len(registry.get('characters', {}))} characters, {len(registry.get('locations', {}))} locations")
        except Exception as e:
            _log(progress, f"[stage1.5] NLP unavailable ({e}); using dialogue-only extraction")
            registry = {"characters": {}, "locations": {}}

    # Stage 2: Extract
    if stage >= 2:
        _log(progress, "[stage2] Resolving period inheritance")
        effective_periods = resolve_periods(scenes)

        _log(progress, "[stage2] Classifying locations")
        result.global_location_assets, result.scene_location_instances = classify_locations(scenes, effective_periods)
        report.location_asset_count = len(result.global_location_assets)

        _log(progress, "[stage2] Extracting characters")
        result.global_characters, result.scene_character_instances, result.scene_background_populations = extract_characters(scenes)
        report.character_count = len(result.global_characters)

        _log(progress, "[stage2] Extracting visual elements and prop interactions")
        result.global_visual_elements, result.scene_visual_elements, result.character_equipment_instances, result.scene_prop_interactions = \
            extract_visual_elements(scenes, result.scene_character_instances)
        report.visual_element_count = len(result.global_visual_elements)

        validate_records(result.global_characters)
        validate_records(result.global_location_assets)

        # Stage 2 LLM enhancement (optional)
        if stage >= 3 and use_llm:
            _log(progress, "[stage2-llm] Initializing semantic router")
            try:
                from .llm.deepseek_client import DeepSeekClient
                from .llm.semantic_router import SemanticRouter
                client = DeepSeekClient.from_env()
                cache_mgr = None
                if llm_cache_dir:
                    from .llm.cache_manager import LlmCacheManager
                    cache_mgr = LlmCacheManager(llm_cache_dir)
                router = SemanticRouter(client=client, cache_mgr=cache_mgr)

                _log(progress, f"[stage3] Routing {report.shot_count} shots through LLM")
                for scene in scenes:
                    context = []
                    for shot in scene.shots:
                        result_dict = router.route_shot(
                            registry, scene.scene_id, shot.shot_id, shot.content, context
                        )
                        # Apply routing results to shot record
                        for update in result_dict.get("sdjs_updates", []):
                            path = update.get("target_path", [])
                            payload = update.get("payload")
                            if "spatial_path" in str(path) and isinstance(payload, list):
                                shot.spatial_path = payload
                            if "characters" in str(path) and isinstance(payload, list):
                                shot.character_ids = payload
                        for update in result_dict.get("smjs_updates", []):
                            path = update.get("target_path", [])
                            payload = update.get("payload")
                            if "semantic_attributes" in str(path) and isinstance(payload, dict):
                                for gc in result.global_characters:
                                    if str(gc.character_id) in str(path):
                                        gc.semantic_attributes.update(payload)
                                        break
                        context.append({"shot_id": shot.shot_id, "content": shot.content})
                _log(progress, "[stage3] Shot routing complete")
            except Exception as e:
                _log(progress, f"[stage3] LLM routing unavailable ({e})")
                report.warnings.append(f"stage3_llm_unavailable:{e}")
    else:
        report.warnings.append("stage2_outputs_require_stage_2_or_higher")

    if output_dir:
        export_output_package(
            scenes=result.scenes,
            report=result.report,
            output_dir=output_dir,
            global_characters=result.global_characters,
            global_location_assets=result.global_location_assets,
            global_visual_elements=result.global_visual_elements,
            scene_character_instances=result.scene_character_instances,
            scene_location_instances=result.scene_location_instances,
            scene_visual_elements=result.scene_visual_elements,
            character_equipment_instances=result.character_equipment_instances,
            scene_prop_interactions=result.scene_prop_interactions,
            scene_intention_analyses=result.scene_intention_analyses if hasattr(result, 'scene_intention_analyses') else None,
            scene_beats=result.scene_beats if hasattr(result, 'scene_beats') else None,
            reviews=result.reviews,
            warnings=result.extraction_warnings,
        )
        _log(progress, f"[export] Output written to {output_dir}")

    return result


def _log(progress: Callable[[str], None] | None, message: str) -> None:
    if progress is not None:
        progress(message)
    logger.info(message)

