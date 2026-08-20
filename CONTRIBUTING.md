# Contributing to ModelRank

ModelRank is independent and community-run. You do not need to be an engineer to help.
Most of the work that grows this project is not code.

## Non-code contributions (welcome)

These move the project as much as any pull request:

- **Write or share.** Post about ModelRank on Reddit, Hacker News, X, or your blog.
  Link back to `https://rankmodel.github.io`. A good writeup beats a silent star.
- **Coverage tips.** Tell us which models we missed in the
  [Missing Models discussion](https://github.com/rankmodel/rankmodel.github.io/discussions/4).
- **Vote on weights.** Weigh in on the
  [Efficiency weight vote](https://github.com/rankmodel/rankmodel.github.io/discussions/3).
- **Debate the philosophy.** Join
  [The Great Debate](https://github.com/rankmodel/rankmodel.github.io/discussions/5).
- **Documentation.** Fix a typo, clarify the methodology, or translate the README.
- **Design.** Badges, the social card, or UI polish. Open an issue with a mock.
- **Report data issues.** A wrong score, a stale model, a broken link. File an issue.

## All-contributors

We use the [all-contributors](https://allcontributors.org) spec so credit is explicit.
Every contribution type — code, docs, design, ideas, social media, bug reports,
translation, mentoring — is recognized in the README contributors table.

To add yourself after contributing, either:

- Comment on your PR/issue with: `@all-contributors please add @yourhandle for
  <code,docs,ideas,content,social,design,bug>`; the bot updates `.all-contributorsrc`
  and the table for you, or
- Edit `.all-contributorsrc` directly and run `npx all-contributors generate`.

The contributor list is machine-owned: never hand-edit the generated table, edit the
`.all-contributorsrc` file instead.

## Code contributions

1. Find a [`good first issue`](https://github.com/rankmodel/rankmodel.github.io/labels/good%20first%20issue)
   or open one to discuss your idea first.
2. Set up the environment:

   ```bash
   python -m venv venv && source venv/bin/activate
   pip install -e .
   cp .env.example .env   # add HF_TOKEN for higher rate limits
   ```

3. Make your change with tests:

   ```bash
   python -m pytest tests/ -q
   ```

4. Open a PR. Describe the why, not just the what. Link the related discussion if any.

## Code of conduct

Be decent. We are ranking other people's models; critique the method, not the maker.
