"""Sarvam Meeting Transcriber — timestamped transcript + AI summary."""
import os, tempfile
from pydub import AudioSegment
from dotenv import load_dotenv
from sarvamai import SarvamAI
from rich.console import Console
from rich.progress import track

load_dotenv()
console = Console()
client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
CHUNK_MS = 25000

def transcribe_meeting(audio_path, language="hi-IN", output="transcript.txt"):
    audio = AudioSegment.from_file(audio_path)
    chunks = [(i/1000, audio[i:i+CHUNK_MS]) for i in range(0, len(audio), CHUNK_MS)]
    lines = []
    with tempfile.TemporaryDirectory() as tmp:
        for start, chunk in track(chunks, description="Transcribing..."):
            p = f"{tmp}/c.wav"; chunk.export(p, format="wav")
            with open(p, "rb") as f:
                r = client.speech_to_text.transcribe(file=f, model="saaras:v3", language_code=language)
            m, s = divmod(int(start), 60)
            lines.append(f"[{m:02d}:{s:02d}] {r.transcript}")
    transcript = "\n".join(lines)
    r = client.chat.completions(messages=[
        {"role":"system","content":"Summarize key points, decisions and action items from this meeting."},
        {"role":"user","content":transcript[:4000]}], model="sarvam-m")
    summary = r.choices[0].message.content
    with open(output, "w") as f:
        f.write(f"=== SUMMARY ===\n{summary}\n\n=== TRANSCRIPT ===\n{transcript}")
    console.print(f"[green]Saved to {output}[/green]")
    console.print(f"\n[bold]Summary:[/bold]\n{summary}")

if __name__ == "__main__":
    import sys
    transcribe_meeting(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "hi-IN",
                       sys.argv[3] if len(sys.argv)>3 else "transcript.txt")
