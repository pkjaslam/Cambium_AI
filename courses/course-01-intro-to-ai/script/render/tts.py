import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from narration import N
import edge_tts

VOICE = "en-IN-NeerjaExpressiveNeural"
async def one(i):
    out = os.path.expanduser(f"~/build/video/audio/a-{i+1:02d}.mp3")
    await edge_tts.Communicate(N[i], VOICE, rate="-4%").save(out)
    return out
async def main(a, b):
    for i in range(a, b):
        for attempt in range(3):
            try:
                await one(i); break
            except Exception:
                if attempt == 2: raise
                await asyncio.sleep(2)
        print(i+1, end=" ", flush=True)
asyncio.run(main(int(sys.argv[1]), int(sys.argv[2])))
print("done")
