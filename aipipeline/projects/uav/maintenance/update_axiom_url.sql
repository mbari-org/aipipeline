--replace the string mantis.shore.mbari.org/UAV/Level-1 with  mbari-uav-data.svx.axds.co in the media_files column
UPDATE tator_online.public.main_media
SET media_files = replace(media_files::TEXT, 'mantis.shore.mbari.org/UAV//Level-1', 'mbari-uav-data.svx.axds.co')::jsonb
WHERE media_files::TEXT LIKE '%mantis.shore.mbari.org/UAV//Level-1%';