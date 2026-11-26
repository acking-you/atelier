# Changelog

Notable changes to the works and the shared code. Renders are not versioned
here; each work's page says which version was delivered when.

## Unreleased

- **Renders archived in Google Drive** under `atelier/<work>/` through the rclone
  remote `gdrive:` (`AGENTS.md` › Assets and storage): 《好想爱这个世界啊》 in
  `atelier/haoxiang/`, the earlier 《我离孤单几公里》 films in `atelier/woligudan/`.
  All of them are shared publicly (anyone with the link); the links are on the
  work pages, [haoxiang](docs/works/haoxiang.md) and [woligudan](docs/works/woligudan.md).
- **Repository created** with its first work, 《好想爱这个世界啊》: the version 4
  film (`hx/`, code-drawn chalk, one continuous drawing), the anime cut's plan,
  key frames and logs (`gx/`, generated clips not kept), the version 3 pictures
  (`hx/art/`), the earlier versions' code (`hx/_attic/`), the recording, its
  lyrics and metadata (`reference/haoxiangaizhegeshijie/`).
- **Shared code** trimmed to what the films use: `mv/engine/palette.py`,
  `mv/engine/prims.py`, and the encoding helpers as `mv/encode.py` (formerly part
  of the previous project's `mv/render.py`; `_plan_chunks` is now `plan_chunks`).
