# Reference review: Kristenkristen/Chemtrails

Source repository: `https://github.com/Kristenkristen/Chemtrails`

Reviewed read-only on 2026-07-19.

## What the repository actually implements

The repository calls the project `phantom-touch-bridge`. It bypasses a browser controller for toys whose official share flow provides a browser-openable remote URL containing a session token.

Documented architecture:

```text
host phone / toy owner
        ↕
brand WebSocket relay
        ↕
Python controller / AI
```

For the implemented MonsterParty backend, the flow is:

1. token comes from a URL such as `https://www.monsterparty.cn/remote/<TOKEN>`;
2. REST request resolves the token into `socket_url`, session ID, and user ID;
3. Python connects to the WebSocket with the expected Origin;
4. an application-level join message is sent;
5. server messages provide a sender file descriptor/device handle and device-ready state;
6. control uses an operation message containing a ten-element integer `vib` array;
7. an application heartbeat is sent roughly every nine seconds;
8. the library's built-in WebSocket ping is disabled.

The implemented example is for Ankni/MonsterParty. The README explicitly says brands that require the controller app and do not expose a browser-openable share link are not directly supported.

## Why it matters for the forum screenshot

The forum screenshot mentioned:

- share link;
- REST API session lookup;
- WebSocket connection;
- a ten-element `vib` array;
- 0-100 intensity.

That description matches Chemtrails' documented MonsterParty protocol extremely closely. Therefore the screenshot is likely describing this repository, the same backend family, or a derivative implementation.

This is useful evidence for a **possible architecture**, but it is not evidence that Cachito uses the same endpoint, op codes, ten-element array, or motor mapping.

## Direct compatibility with Cachito

Current answer: **not directly compatible from the evidence available**.

Chemtrails requires a remote URL that can be opened in an ordinary browser and exposes a token in the URL. Cachito currently exposes only a six-character code inside the official app, and the successful remote-controller test required another Cachito app.

Consequences:

- `ankni_client.py` cannot simply be run with the Cachito code;
- MonsterParty REST endpoints and op codes must not be copied;
- the ten-element `vib` array must not be assumed for Cachito;
- Cachito may still use a similar hidden REST + WebSocket session internally.

## Reusable parts

### 1. Investigation order

Chemtrails' `AI_GUIDE.md` gives a strong generic sequence:

1. observe session creation/exchange;
2. identify REST/XHR response containing a WebSocket URL or session metadata;
3. inspect WebSocket frames;
4. find join, ready, control, stop, and heartbeat messages;
5. identify dynamic values supplied by the server;
6. keep the socket alive in one daemon rather than reconnecting per command.

For Cachito, this observation must happen at the app level rather than through a browser share page.

### 2. Controller separation

The generic template separates:

- `fetch_session()`;
- `build_join_msg()`;
- `build_control_msg()`;
- device-ready parsing;
- heartbeat;
- local command IPC.

That is a good shape for a later Cachito implementation once the real fields are known.

### 3. Failure modes worth testing

- session code may expire or be single-use;
- joining may require a mandatory first message;
- device-ready state may arrive separately from connection state;
- brand heartbeat may be required even when the WebSocket transport itself is healthy;
- protocol-level heartbeat may conflict with library keepalive;
- reconnecting for every command may invalidate or consume the invitation.

## Cachito-specific adaptation plan

Do not write the controller yet. First capture one official two-phone session and answer:

1. What request is sent when the host app creates the six-character code?
2. What request is sent when the controller app submits it?
3. Does either response return `ws://` / `wss://`, session IDs, user IDs, or device IDs?
4. What first frame is sent after connection?
5. What frame marks the accessory as ready?
6. What changes when suction, piston, pause, and gravity controls are used?
7. What heartbeat and expiry behavior exists?

If Cachito follows the same architectural family, the Chemtrails generic template can then be adapted by filling in Cachito's real endpoint, headers, message builders, readiness conditions, heartbeat, and safe stop command.

## Ranking impact on current route decision

Chemtrails raises the confidence of Route A (official remote session) as a practical architecture, because a complete AI-to-cloud-to-host-app implementation exists for another brand.

It does **not** prove Route A is immediately available for Cachito. The current route order remains:

1. document Cachito's own session exchange;
2. prefer remote-session emulation if the protocol is observable and stable;
3. otherwise identify whether `710002..` is phone advertising or accessory advertising;
4. then choose advertisement replay or direct GATT.

## Files reviewed

- `README.md`
- `AI_GUIDE.md`
- `template.py`

No code from Chemtrails has been copied into the Cachito project.
