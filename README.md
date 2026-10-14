# autopoiesis

A portable method for maintaining and improving useful agent capabilities within human-owned goals.

Status: initial public package published on 2026-10-14; subsequent local edits are release candidates until independently published and verified. No background service, installer, publisher or self-modification authority is provided. The method can be used with an existing executor.

| Need | Read |
|---|---|
| Capability contract and improvement protocol | [METHOD.md](METHOD.md) |
| Read-only route sensor | [routecheck.py](routecheck.py) |
| Neutral regression cases | [test_routecheck.py](test_routecheck.py) |

Run `python -B routecheck.py --root <instance-root> --manifest <bindings.json>` for a JSON observation. Exit 0 means the declared routes checked successfully, 1 means a broken route, and 2 means an invalid specification or incomplete collection. This proves neither runtime adoption nor business value.

Manifest format: `{"version":1,"routes":[{"id":"catalog","entry":"MAPA.md","map":"catalog/MAPA.md","registry":"catalog/items.json","collections":["items"]}]}`. All paths are root-relative. The entry must explicitly mention the map; the map must explicitly mention the registry. Paths inside code spans or Markdown links are accepted. Bindings belong to the instance and are not duplicated capability records.

Tests run with `python -B test_routecheck.py --fixtures <existing-test-parent>`. They create an isolated fixture directory, retain it as evidence and never modify a live instance.

Dependencies: Python standard library. No network access. Ownership, schedules, credentials and private evidence stay in each instance. Apply changes only through its authorized writer.
