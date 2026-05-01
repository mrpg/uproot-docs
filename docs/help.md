# Getting help

Relax and move slowly. Most problems with experiments turn out to be small things — a missing field, a wrong variable name, a misunderstood page method. Taking a step back and reading carefully will almost always get you further than rushing. The steps below are in order of what to try first.

## 1. Read the documentation

Start here. This documentation covers all of uproot's features with explanations and code examples. Use the search function and navigate by topic — chances are your question is already answered. Pay particular attention to the [reference section](reference/fields.md) for detailed specifications.

For complete, runnable examples, browse the [:material-github: uproot-examples](https://github.com/mrpg/uproot-examples/tree/master) repository.

Advanced users can also browse the [:material-github: uproot source code](https://github.com/mrpg/uproot) directly and search through it for particular keywords. Sometimes reading the implementation is the fastest way to understand a behavior.

## 2. Ask a coding agent

AI coding agents like [Claude Code](https://claude.ai/code), [Codex](https://openai.com/index/introducing-codex/), and similar tools are excellent at helping with uproot. They can debug experiments, explain page lifecycle behavior, write form logic, and work through multiplayer synchronization issues.

If your coding agent supports skills (Claude Code, Codex, and others do), install the **uproot skill** for best results:

:material-github: [mrpg/uproot-skill](https://github.com/mrpg/uproot-skill)

This skill gives the agent deep knowledge of uproot's API, page lifecycle, fields, SmoothOperators, and multiplayer features. See the [installation guide](getting-started/installation.md#set-up-ai-assisted-development) for setup instructions.

If your coding agent does not support skills, this prompt provides useful context:

> I'm building a behavioral experiment using the uproot framework (https://github.com/mrpg/uproot). Documentation is at https://uproot.science/ and example experiments are at https://github.com/mrpg/uproot-examples. The documentation source is at https://github.com/mrpg/uproot-docs — you can clone it for full context.
>
> [Describe your problem here.]

!!! tip

    Cloning the [uproot-docs](https://github.com/mrpg/uproot-docs) repository alongside your project gives any coding agent direct access to all documentation source files, which tends to produce much better answers.

## 3. Email Max and Holger

If you've read the docs, asked an AI, and are still stuck — write to us. Email **both** Max and Holger jointly so that whoever is available can respond and neither of us loses context. You can find our contact details on the [legal information](legal.md#contact) page.

We are happy to help, and we mean it. Especially if your question reveals a gap in the documentation, your experience helps us improve uproot for everyone.

!!! note

    All issues raised via email are treated anonymously if they lead to documentation updates.

## 4. File an issue on GitHub

If you've identified a concrete bug in uproot — something that is broken, not just unclear — please [open an issue on GitHub](https://github.com/mrpg/uproot/issues). There is a low bar for filing issues: you don't need to follow any particular template or protocol. Just describe what you observed and what you expected. A minimal reproduction helps, but is not required.

This step is specifically for bugs, not for usage questions. For usage questions, email us instead.

## Why there is no forum

You might wonder why uproot has no community forum, Discord server, or discussion board. This is a deliberate choice, not an oversight.

**Correct answers should live in one place.** A forum accumulates answers of varying quality, age, and correctness. Over time, outdated advice coexists with current advice, and users cannot tell which is which. Documentation, by contrast, can be maintained as a single source of truth. When we learn about a common problem or a clever approach, we add it to the docs — where it stays correct and findable.

**Forums fragment knowledge.** The same question gets asked and answered differently across multiple threads. Search engines surface forum posts that may contradict the documentation. This is confusing for newcomers and costly for everyone.

**Quality requires curation.** A forum needs active moderation to remain useful — removing spam, correcting wrong answers, merging duplicates, updating stale threads. This is a substantial ongoing commitment. Unmoderated forums degrade quickly and can become actively harmful when incorrect answers go unchallenged.

**Security and operational burden.** Running a forum means maintaining another piece of infrastructure with user accounts, authentication, and stored data. This creates attack surface and privacy obligations that are disproportionate for a project of uproot's size.

**Direct contact scales better than you'd think.** For a focused framework like uproot, the volume of genuinely novel questions is manageable. Most questions are already answered by the docs or an AI agent. The few that remain are often interesting enough that we want to hear about them directly — they tend to reveal real gaps in the documentation or the framework itself.

**Your questions improve the docs.** When you email us, your problem often points to something we can clarify or document better. This benefits all future users, not just the people who happen to read a specific forum thread. Every question that reaches us is an opportunity to make uproot easier to use for everyone.

So: if you're stuck, just write to us. We'd rather answer your email and improve the docs than maintain a forum.
