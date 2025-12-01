# AI USAGE

## Where AI helped
- AI was mainly used to accelerate development and explore design options. I used it to better understand the skeleton, plan development phases, explore the pros and cons of the tech stack choice, evaluate different heuristic approaches, and resolve/detect errors and bugs.

## Prompts or strategies that worked
- Specifically asked AI to check NBA's website and learn about their heuristics design, and suggest a few other options.
- Asked it to analyze the `match_events.json`, counting reoccurrences and trends to help me decide on a ranking approach that suits the data.
- Asked it to highlight the areas/functions that are essential and need to be tested while maximizing coverage.

## Verification steps (tests, assertions, manual checks)
- Debugging as I progressed: each time I had a new main function working I wrote a debugging script (e.g. `debug_assets.py`) and ran it through the terminal to verify results visually.
- Manual checks of uploading `story.json` through the preview with various Top N cases.
- At the testing phase, assertions were used based on my understanding of the functionality of different methods.

## Cases where you chose **not** to use AI and why
- Making design decisions: I specifically asked the AI to only analyze or research rather than choose. Even after suggesting multiple options, I argued with it by introducing scenarios where one approach might not be ideal (e.g., a heuristic based solely on scores might cause events at minute 90+ to sound less important even if it changes the whole game).
- Determining tests: AI tended to be very tedious with testing, recreating almost all scenarios even when we had good function coverage, sometimes producing redundant code.