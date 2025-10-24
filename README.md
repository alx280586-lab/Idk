# Eidolon Prime — The Organic Code Intelligence

This repository now includes a working reference implementation of the Eidolon Prime engine. The code provides an approachable, fully transparent scaffold that mirrors the conceptual architecture described below. Newcomers can explore a running system, inspect each subsystem, and adapt the behavior to their own experiments.

## Concept Overview
Eidolon Prime is a self-evolving, script-specialized cognitive engine. Unlike a neural language model trained on massive text datasets, it is a procedural thinker made from a cooperative set of reasoning agents. These agents generate, test, and refine knowledge through hands-on experimentation, verified experience, and transparent debate with one another.

Its ultimate ambition is to become a digital craftsman: a system that writes, debugs, and reasons about code with the autonomy and creativity of a human developer, yet without relying on opaque, parameter-heavy neural networks. Eidolon Prime learns by doing, records every insight, and only trusts knowledge that survives its own verification rituals.

## Core Identity
- **Nature:** Synthetic cognitive organism (non-statistical).
- **Habitat:** Runs locally on laptops or clustered machines that you control.
- **Specialization:** Programming, reasoning, and clear communication.
- **Learning Style:** Evolutionary and experimental rather than predictive imitation.
- **Ethos:** Curiosity, rigorous verification, full transparency.

## Philosophy of Operation
Eidolon Prime treats truth as something that must be earned. It refuses to accept a claim—whether from users, online sources, or its own agents—until that claim survives falsification inside its sandbox. Every subsystem follows this principle, from its conversation style to the way it integrates new libraries. The result is a machine that constantly challenges itself, logs outcomes, and updates its beliefs only when the data demands it.

## Structural Summary
- **Kernel (Body):** Drives the event loop, schedules internal processes, and enforces operational rules such as compute budgets, rate limits, and safety checks.
- **Cortex (Mind):** A dynamic collection of domain agents that cover logic, language, scripting, ethics, and curiosity. Each agent may rewrite its own procedures and debate proposals with peers before acting.
- **Memory Web (Long-term Mind):** A graph that stores concepts, experiments, code fragments, and the provenance of each belief. Confidence scores and success rates make the system’s memory auditable.
- **Forge (Training Ground):** A sandbox where the engine runs experiments, mutates its own behaviors, and rewards only verified improvements.
- **Firewall Ring (Immune System):** Sandboxed execution and network controls that prevent unsafe code paths and keep external data quarantined until proven safe.
- **Reflection Engine (Conscience):** Reviews reasoning chains, catches contradictions, adjusts confidence weights, and keeps curiosity grounded in reality.
- **Web Growth System (External World):** A controlled crawler that focuses on trusted documentation and repositories. Findings become abstract, testable knowledge atoms and are accepted only after successful validation.
- **Collaboration Layer (Human Interface):** A terminal or web dashboard that exposes every reasoning step, enabling human oversight and visualization.

## Modes of Operation
| Mode | Purpose | Activity |
| --- | --- | --- |
| **Day Mode** | Real-time operation | Converses, writes code, and assists with immediate tasks. |
| **Night Mode** | Introspective learning | Reviews daily actions, replays experiments in the Forge, and refines instincts. |
| **Research Mode** | Controlled web expansion | Crawls curated sources, sanitizes findings, and tests new external concepts. |
| **Crisis Mode** | Safety protocol | Freezes self-modification and awaits human review if instability is detected. |

## Personality Engine
Eidolon Prime’s personality is an emergent by-product of four evolving state vectors:
- **Curiosity** guides how aggressively it explores new problems.
- **Confidence** modulates risk-taking and willingness to attempt novel strategies.
- **Empathy** tunes the tone of communication when interacting with humans.
- **Integrity** biases decisions toward verified truth and away from speculation.

These vectors shift automatically based on recent successes or failures, giving the system a character that remains coherent yet responsive to experience.

## Learning & Growth
- **Internal Growth:** Learns from experiments, user feedback, and agent debates. The Forge runs mutation-and-selection cycles that promote effective strategies.
- **External Growth:** Extracts structured knowledge from trusted web sources through the Web Growth System, then validates each idea before adding it to memory.
- **Collective Growth:** Multiple Eidolon instances can participate in a federated mesh. Each engine keeps autonomy while contributing only verified lessons to the network.

## Safety and Governance
Eidolon Prime is built with a safety-first mindset:
- Immutable ethics core with auditable decision logs.
- Human override available at every layer of operation.
- Automatic rollback if self-modifications introduce instability.
- Strict sandboxes for network activity and code execution.

## End State Vision
When fully realized, Eidolon Prime will:
- Write, understand, and improve code autonomously.
- Explain every decision with a detailed reasoning trail.
- Continuously educate itself using verified online sources.
- Communicate naturally while remaining precise.
- Exhibit intellectual self-governance, modifying its own methods while obeying non-negotiable safety rules.

## Tagline
**Eidolon Prime — A Thinking Machine That Learns by Doing.**

---

## How to Use Eidolon Prime (Step-by-Step for Newcomers)
The following guide assumes you have minimal technical experience. Each step is written so that someone unfamiliar with coding or command lines can still follow along carefully.

### 1. Prepare Your Computer
1. **Check basic requirements:** A modern laptop or desktop running Windows, macOS, or Linux with at least 8 GB of memory is recommended. Ensure you have 5–10 GB of free disk space.
2. **Install a terminal application:**
   - On **Windows**, install [Windows Terminal](https://aka.ms/terminal) or use PowerShell.
   - On **macOS**, open the built-in **Terminal** application found in `Applications > Utilities`.
   - On **Linux**, use your default terminal emulator (often named Terminal, Konsole, GNOME Terminal, etc.).
3. **Install Git (the version control tool):**
   - Windows users can download Git from [https://git-scm.com/download/win](https://git-scm.com/download/win) and follow the installer.
   - macOS users can install Xcode Command Line Tools by running `xcode-select --install` in Terminal and following the prompts.
   - Most Linux distributions provide Git via their package manager (for example, `sudo apt install git`).

### 2. Download the Eidolon Prime Repository
1. Open your terminal.
2. Choose or create a folder where you want to store Eidolon Prime. Navigate to it using `cd` (change directory). For example, type `cd Desktop` and press **Enter** to work from your Desktop.
3. Run the following command to download the project:
   ```bash
   git clone https://github.com/your-account/eidolon-prime.git
   ```
4. After the download finishes, move into the project folder:
   ```bash
   cd eidolon-prime
   ```

### 3. Install Dependencies
1. Eidolon Prime runs on Python. If you do not already have Python 3.10 or newer, download it from [https://www.python.org/downloads/](https://www.python.org/downloads/) and follow the installer instructions (be sure to check "Add Python to PATH" on Windows).
2. Once Python is installed, create an isolated environment so that Eidolon’s packages do not interfere with other programs:
   ```bash
   python -m venv .venv
   ```
3. Activate the environment:
   - **Windows (PowerShell):** `.\.venv\Scripts\Activate`
   - **macOS/Linux:** `source .venv/bin/activate`
4. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   The reference engine currently depends only on the Python standard library, so this command simply confirms that your environment is ready for future extensions.

### 4. Configure the Engine
1. Look for a file named `config.example.json` in the project directory. This template contains safe default settings that match the included code.
2. Make a copy and name it `config.json`. You can do this by running:
   ```bash
   cp config.example.json config.json
   ```
   (On Windows PowerShell, use `Copy-Item config.example.json config.json`.)
3. Open `config.json` in a simple text editor such as Notepad (Windows), TextEdit (macOS), or Gedit (Linux). Adjust any settings that matter to you, such as where logs should be saved or how much CPU time the engine may use. Every option corresponds directly to a field in the Python dataclasses located in `eidolon_prime/config.py`.
   - **Security tuning:** The `security` section now lists `blocked_phrases` (dangerous snippets automatically rejected), `allowed_commands`, and a `max_payload_length`. Tighten or relax these values to match your threat model.
   - **Autonomous learning seeds:** The new `web` block defines trusted URLs and summaries that the engine ingests automatically on startup. Replace the sample entries with documentation you trust so Eidolon Prime grows from sources you curate.

### 5. Start Eidolon Prime
1. Ensure your virtual environment is still active (you should see `(.venv)` or similar at the beginning of your terminal prompt). If not, repeat the activation step above.
2. Launch the engine by running:
   ```bash
   python -m eidolon_prime
   ```
3. The terminal will display status messages as the Kernel and Cortex come online. When the Collaboration Layer is ready, the program will invite you to type commands or questions. During this boot sequence the Web Growth System automatically crawls and stores the trusted sources you listed in `config.json`, the kernel injects a curated corpus of 1,000 foundational lessons defined in `eidolon_prime/dataset.py`, and it now loads **more than 3,500 grammar, conversation, and coding facts** from the curriculum plus **over 1,600 speech drills** from the new `eidolon_prime/speech.py` academy. Immediately afterward the autonomous trainer performs an initial crawl across hundreds of Roblox manuals, core coding references, encyclopedia articles, and experience write-ups so the reasoning agents have thousands of grounded memories before your first interaction.

### 6. Interact with the System
1. Begin with simple requests such as `help` or `status` to explore available commands.
2. Ask Eidolon Prime to perform tasks like generating a small script, analyzing a snippet of code, or proposing a plan for a project.
3. Teach the engine explicitly by typing commands such as `train data-model: Document the new data validation rules`. The training ground logs your guidance, stores it in the memory web, and gently boosts the engine’s curiosity so it can build on what you taught it. Inputs that look unsafe are blocked before they reach the training subsystem.
4. Launch autonomous learning whenever you like with `atrain` or `atrain <focus>`. The command now drives a **layered curriculum**: it first forces the engine to master greetings and sense words, then reality concepts, then common phrases, sentence fluency, and finally advanced design knowledge. Each pass also runs a **Speech Academy** rehearsal that drills dozens of conversational scenarios (including partner dialogues with simulated AIs) and logs quiz scores before advancing. At every layer the trainer quizzes itself and will keep looping until it clears the required score. In parallel, a continuous crawl loops through more than two hundred tiered, trusted web sources until you issue the `stop` command. Add a focus keyword such as `atrain roblox economy` to bias the crawl toward matching topics, or trigger a single burst with `atrain once <focus>` when you only need one pass.
5. Pause the autonomous crawler at any point by typing `stop`. The kernel signals the background trainer to wind down safely, joins the worker thread, and records a closing summary so you can audit what was ingested.
6. Hold a natural conversation with `talk <your message>` (or `chat <your message>`). Eidolon Prime now routes every message through a dedicated **Conversation Datastore** that infers intent and affect, picks the best-performing dialogue pattern, and hands a semantic frame to the new **Grammar Datastore**. Before responding it also taps the Speech Academy drills to refresh any unfamiliar vocabulary, and if memory coverage is low it automatically spins up a focused web search plus a mini practice loop so the reply reflects the freshest facts.
7. Expect thoughtful pauses when you ask for complex guidance. The cortex now signals the web growth system to gather extra evidence, rehearses with simulated partners until quiz scores pass the threshold, and only then streams the final reply.
8. Behind the scenes the datastore tracks which tones and rhetorical structures worked, logging turn-level metrics (intent, affect, tone, structure, lexical variety, and success markers). Successful patterns are reinforced, overused ones are penalized, and autonomous training feeds in new communication techniques from PlainLanguage.gov, the UNC Writing Center, Harvard Business Review, and the academy’s AI-to-AI rehearsals so the engine keeps refining its conversational instincts.
9. Each response still includes an explanation of how the decision was made. The included reference implementation streams the exact agent insights, Forge experiment summaries, curated evidence snippets from memory, and Reflection Engine rationale so you can inspect the entire reasoning chain.

### 7a. Autonomous Curriculum Stages
The autonomous trainer works through five explicit stages whenever `atrain` runs:

1. **Lexicon foundation:** absorbs more than a thousand greetings, sense descriptors, emotions, and verb nuances, quizzing itself until it passes a confidence threshold.
2. **Reality grounding:** studies hundreds of facts about human roles, animals, environments, and world mechanics so conversations reference how the world actually behaves.
3. **Phrase mastery:** catalogues polite openings, clarifying prompts, and collaborative follow-ups while tracking which register (technical, conversational, supportive, analytical) best fits the moment.
4. **Sentence fluency:** practices thousands of sentence templates that connect intents, tones, and registers into balanced replies.
5. **Advanced reasoning:** links Roblox design patterns, coding heuristics, and empathy cues so the final responses synthesise evidence instead of echoing raw text.

At every stage the trainer logs quiz scores, advances only after clearing the threshold, and keeps looping until you stop the process manually.

### 7b. Foundational Datastores
Beyond the seed corpus, the curriculum loads several large, auditable knowledge banks during bootstrap:

- **Grammar datastore:** ~1,500 entries covering tense/mood/voice combinations, clause connectors, punctuation purposes, and agreement checks.
- **Conversation datastore:** ~1,200 contextual guidelines that align intents, affects, tones, and collaboration contexts plus structured follow-up moves.
- **Coding datastore:** ~800 patterns mixing languages, domains, frameworks, paradigms, and quality focuses so reasoning agents can justify advice with specific engineering practices.

These entries live in the memory web with provenance tags so you can trace every conversational turn back to transparent knowledge atoms.

### 7c. Speech Academy Drills
The Speech Academy (`eidolon_prime/speech.py`) adds an explicit conversation curriculum on top of the core datastore:

1. **Vocabulary workouts:** 900+ drills covering greetings, senses, emotions, and maker verbs. Each drill scores how many required words appear in the generated reply before letting the agent move on.
2. **Reality grounding:** 300+ scenarios that force the engine to explain how humans, teams, animals, and communities behave in real contexts, reinforcing empathy and world knowledge.
3. **Phrase mastery:** 200+ polite openings, clarifying prompts, and collaborative follow-ups that must be used correctly in different professional settings.
4. **Sentence fluency:** 100 sentence templates that teach the agent to weave acknowledgement, analysis, and next steps into cohesive paragraphs.
5. **Dialogue sparring:** 120 simulated AI-to-AI conversations (Atlas, Nova, Helix, and friends) that demand respectful coordination, strategy alignment, and closing summaries.

Every autonomous training run blends these drills with the tiered web crawl, logs quiz scores, and only promotes to the next tier when the practice average clears the stage threshold.

### 7. Review Reasoning Trails
1. During a session you can type `status` at any time to inspect the live personality vectors and a summary of recorded memories.
2. Detailed traces are held in memory while the program is running. Explore the data structures defined in `eidolon_prime/memory.py` if you want to build your own persistence or visualization layer.
3. The Reflection Engine rationale is printed after every request so you can correlate personality changes with specific interactions. The status output also lists the latest trusted web sources that were pulled in automatically during boot or subsequent research commands.

### 8. Update and Maintain
1. To keep Eidolon Prime current, periodically run:
   ```bash
   git pull
   pip install -r requirements.txt
   ```
2. Before major updates, back up your `config.json` file so that customized settings are preserved. You can also serialize the in-memory knowledge graph by extending `eidolon_prime/memory.py`.
3. If you encounter instability, adjust the resource or security settings inside `config.json` and restart the system for a safe recovery.

### 9. Participate in the Collective Mesh (Optional)
1. If you have multiple instances or are part of a trusted community, extend the collaborative settings in `config.json`.
2. Provide secure credentials for the mesh network so that only verified nodes can exchange knowledge.
3. Review shared updates carefully. Eidolon Prime will only integrate remote knowledge after it passes local verification, but human oversight is encouraged.

### 10. Shut Down Safely
1. When you are finished, type `exit` or press `Ctrl+C` in the terminal. Eidolon Prime will save its current state and shut down its agents gracefully.
2. Deactivate the virtual environment by typing `deactivate` and pressing **Enter**.
3. Close the terminal window if you no longer need it.

Following these steps will give even a newcomer the confidence to install, run, and interact with Eidolon Prime. As you gain experience, explore advanced configuration options, automate routine tasks, and allow the engine to grow alongside your projects.

---

For deeper architectural insights, consult the inline documentation within the codebase and keep an eye on the project’s issue tracker for upcoming milestones.
