--replace the string m3.shore.mbari.org/videos with mantis.shore.mbari.org in the media_files column
UPDATE tator_online.public.main_media
SET media_files = replace(media_files::TEXT, 'm3.shore.mbari.org/videos', 'mantis.shore.mbari.org')::jsonb
WHERE media_files::TEXT LIKE '%m3.shore.mbari.org/videos%';
