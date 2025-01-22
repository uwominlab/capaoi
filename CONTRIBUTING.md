<a name="commits"></a>
## Git Commit Good Practice

### Commit messages

When writing a commit message there are some important things to remember

- Do not assume the reviewer understands what the original problem was.
- Do not assume the code is self-evident/self-documenting.
- Describe why a change is being made.

### Structural split of changes

Keep your git commit history consistent and clear avoiding meaningless commit messages and non-logical functional changes. Ensure that there is only one "logical change" per commit.

- Do not mix code style changes with functional code changes in 1 commit
- Do not mix unrelated functional changes in 1 commit
- Do not put large new features to 1 single commit

To have the history in a consistent state use git technics metioned in
['Rewriting History' Git documentation](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History) to squash/fixup
commits in feature branches.
