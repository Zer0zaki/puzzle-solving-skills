# Network research and contest-interface boundary

## Allowed online research

- Search for general knowledge related to the puzzle's subject, terminology, historical context, scientific facts, language facts, or cultural references.
- Locate and query relevant public databases, dictionaries, corpora, catalogs, maps, academic sources, standards, or reference tables.
- Verify a factual claim or dataset field needed by an internally derived mechanism.
- Follow a user-provided reference URL when it is background material rather than a contest interface or solution source.

Construct queries from the general research question. Prefer topic terms such as a concept, entity class, property, or database field rather than distinctive puzzle wording.

## Prohibited source and solution hunting

Do not use the internet to identify or retrieve:

- the puzzle's contest, source, original page, archived copy, repost, or duplicate;
- official or unofficial solutions, write-ups, answer lists, hint repositories, or discussion threads;
- an answer inferred from search-result snippets;
- matches produced by querying the exact title, distinctive sentence, full clue list, complete puzzle text, or puzzle image;
- reverse-image or visually similar-image results intended to locate the original puzzle.

Do not search a solution site merely to “verify” an answer. Verification must come from the puzzle mechanism, constraints, independent computation, or permitted background facts.

## Contest interface is user-operated only

Never use browser control, an existing authenticated browser session, an in-app browser, page automation, DOM inspection, developer tools, screenshots, clipboard access, or network inspection to collect contest information that the user did not provide.

Do not open or navigate the contest interface on the user's behalf. Do not click buttons, reveal hints, submit answers, inspect locked content, or operate an interactive puzzle. When an interaction is required:

1. describe the exact action the user should perform;
2. state what result, screenshot, or changed state is needed;
3. wait for the user to perform it;
4. treat only the returned material as puzzle evidence.

## Evidence separation

Record online material as `网络背景事实`, with its source and the claim it supports. Do not merge it into `题目直接观察` or use it to silently repair missing puzzle material. A database result may support a transformation or factual mapping, but it does not prove that the intended puzzle mechanism is correct.

Before browsing, record the generic research question. After browsing, record the sources used and the facts imported. Do not include the puzzle title or unique clue text in queries unless the user explicitly changes this policy.

## Accidental contamination

If a result appears to expose the original puzzle, a write-up, a solution, or an answer:

1. do not open additional matching results;
2. do not incorporate the revealed material into the solve;
3. mark the affected route as `来源污染风险`;
4. tell the user what type of material appeared, without repeating the answer;
5. continue only from independently available puzzle evidence and permitted background knowledge.
