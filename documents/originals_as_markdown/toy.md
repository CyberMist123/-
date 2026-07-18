# Controlling a Toy with AI: A Pitfall Record

> Markdown transcription of the previously uploaded `toy.docx`.

## Background

The goal was simple: AI sends a command, a phone broadcasts it via BLE, and a toy executes the action. The toy uses a proprietary BLE protocol, and the official app doesn't expose any API.

## Overall Approach

A computer runs an HTTP server (AI writes commands into a queue via MCP). A phone app polls the server every few seconds, gets the command, encodes it, and broadcasts it via BLE. The toy receives the broadcast and responds.

Sounds simple, right? It was not.

## Pitfalls

### Pitfall 0: Trying to connect via computer Bluetooth directly

I wrote an MCP server script to connect the toy directly from the computer. But the MCP connection kept dropping, throwing context loss errors all the time. Commands would fail mid-way. It was never stable enough to use. Gave up after a lot of frustration.

Then I tried nRF Connect to manually broadcast test packets. Didn't work either — because the encoding algorithm was wrong, the toy didn't recognize anything.

### Pitfall 1: Writing my own encoding algorithm

I thought encoding a command was as simple as turning it into a byte array and broadcasting it. The toy did nothing. After decompiling the official app, I found it uses a C++ native library for encoding, with whitening, CRC, bit reversal, and more. Nothing like a simple byte conversion.

**Lesson:** Don't guess proprietary RF protocols. Just use the official native library.

### Pitfall 2: Wrong broadcast parameters

Comparing with the decompiled official code, several differences stood out:

- Manufacturer ID is 0x00FF, not 0x0000
- The official app doesn't include any Service UUID — pure Manufacturer Data only
- A 5-byte address prefix is prepended before encoding

Fixed them one by one before it finally worked.

### Pitfall 3: Missing configurations

- Forgot `usesCleartextTraffic="true"` in AndroidManifest — HTTP polling broke immediately
- Set broadcast timeout to 0 — it stopped right after starting
- Didn't have all the required permissions — Android 12+ just threw errors

## Final Solution

It's actually quite simple in the end:

1. Extract `libble.so` from the official app, put it in your project's jniLibs folder
2. Write a JNI wrapper class to call its encoding function
3. Broadcast with Manufacturer ID 0x00FF, using the encoded result as data

No Service UUID, no iBeacon format needed.

## Takeaways

- Decompile the official app first — it saves more than half the time
- For proprietary protocols, reuse official code instead of rewriting it
- Stay patient — these problems are often just one small detail away from working

## Recommendation

This method is quite involved and time-consuming. If you just want to control the toy without going through all this, try Intiface first (a universal hardware control middleware). It supports many devices out of the box and is much easier to set up.

Only fall back to this approach if Intiface doesn't work with your device.

## Relevance note for Cachito

This document is a precedent from another proprietary BLE implementation. Its exact manufacturer ID, payload format, native library, and Android details must not be copied to Cachito without evidence. Its reusable lesson is methodological: inspect the official app and avoid guessing encoding.
