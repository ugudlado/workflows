# Format: video

Output: `deliverables/<stem>.mp4` (1280x720, narrated, one slide per audio
clip).

## Build

Requires the slide PNGs from the slides format (build slides first if they do
not exist). Narration comes from each slide's speaker notes: for slide N write
a spoken script (2-4 plain sentences, no citation brackets, no URLs, numbers
written as people say them) to `audio/sN.txt`; slide 1 introduces topic and
audience, slide 10 closes with where the sources are.

```bash
mkdir -p audio seg
say -o audio/s1.aiff -f audio/s1.txt          # repeat for each slide N
```

For each slide, make a clip with the image held for the length of its audio:

```bash
/opt/homebrew/bin/ffmpeg -y -loglevel error -loop 1 -framerate 2 \
  -i <stem>.001.png -i audio/s1.aiff \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:v libx264 -c:a aac -ar 44100 -shortest seg/s1.mp4
```

(PNG names are `<stem>.001.png`..`<stem>.010.png`; pair slide N with `sN.aiff`.)
Concatenate in order:

```bash
printf "file 'seg/s1.mp4'\nfile 'seg/s2.mp4'\n..." > list.txt   # all 10, in order
/opt/homebrew/bin/ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy <stem>.mp4
```

## Verify

`/opt/homebrew/bin/ffprobe -v error -show_entries format=duration -of csv=p=0 <stem>.mp4`
is about the sum of the audio durations (within a second or two) and the file
has one video and one audio stream. Write photo credits to
`<stem>-video-credits.txt`. Keep the intermediates in `audio/` and `seg/`; list
only the .mp4 and credits file as deliverables.
