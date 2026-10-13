-- Synthetic, non-user legacy project used only by IMP-101 integration tests.
-- Schema comes from agent.db.schema.SCHEMA; these rows contain no real credentials/media.
INSERT INTO project (
    id, name, description, story, language, status, thumbnail_url, material
) VALUES (
    'legacy-project-101',
    'Synthetic Migration Fixture',
    'Synthetic fixture only',
    'IMP101_STORY_SENTINEL_NEVER_PERSIST',
    'vi',
    'ACTIVE',
    'https://example.invalid/project-thumb.png',
    'realistic'
);

INSERT INTO character (
    id, name, slug, entity_type, description, image_prompt, reference_image_url, media_id
) VALUES (
    'legacy-character-101',
    'Synthetic Character',
    'synthetic-character',
    'character',
    'Synthetic fixture only',
    'IMP101_CHARACTER_PROMPT_SENTINEL_NEVER_PERSIST',
    'https://example.invalid/character-reference.png',
    'legacy-media-character-101'
);

INSERT INTO project_character (project_id, character_id)
VALUES ('legacy-project-101', 'legacy-character-101');

INSERT INTO video (
    id, project_id, title, description, status, vertical_url, horizontal_url, orientation
) VALUES (
    'legacy-video-101',
    'legacy-project-101',
    'Synthetic Video Container',
    'Execution container; not canonical Film truth',
    'COMPLETED',
    'https://example.invalid/video-vertical.mp4',
    'https://example.invalid/video-horizontal.mp4',
    'VERTICAL'
);

INSERT INTO scene (
    id, video_id, display_order, prompt, image_prompt, video_prompt, character_names,
    vertical_image_url, vertical_image_media_id, vertical_video_url,
    vertical_video_media_id, narrator_text, chain_type, source
) VALUES (
    'legacy-scene-101',
    'legacy-video-101',
    1,
    'IMP101_SCENE_PROMPT_SENTINEL_NEVER_PERSIST',
    'IMP101_IMAGE_PROMPT_SENTINEL_NEVER_PERSIST',
    '0-3s: synthetic camera move; 3-6s: synthetic subject action',
    '["Synthetic Character"]',
    'https://example.invalid/scene.png',
    'legacy-media-scene-image-101',
    'https://example.invalid/scene.mp4',
    'legacy-media-scene-video-101',
    'IMP101_NARRATION_SENTINEL_NEVER_PERSIST',
    'ROOT',
    'root'
);

INSERT INTO request (
    id, project_id, video_id, scene_id, type, orientation, status,
    request_id, media_id, output_url, edit_prompt, source_media_id
) VALUES (
    'legacy-request-101',
    'legacy-project-101',
    'legacy-video-101',
    'legacy-scene-101',
    'GENERATE_IMAGE',
    'VERTICAL',
    'COMPLETED',
    'synthetic-external-request-id',
    'legacy-media-request-101',
    'https://example.invalid/request-output.png',
    'IMP101_REQUEST_PROMPT_SENTINEL_NEVER_PERSIST',
    'legacy-source-media-101'
);

INSERT INTO material (id, name, style_instruction, negative_prompt, scene_prefix)
VALUES (
    'material-101',
    'Synthetic Material',
    'Synthetic style configuration',
    'Synthetic negative prompt',
    'Synthetic scene prefix'
);
