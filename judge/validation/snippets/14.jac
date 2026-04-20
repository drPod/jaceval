This file contains plain English prose, not code.

The task was supposed to be solved in the Jac language, but instead of writing
Jac code, the candidate has written an explanation of what the solution would
look like. There is no archetype, no walker, no edge, no with-entry block, no
semicolons, no braces, no executable content at all. A parser handed this file
will fail at the first token.

In a real solution we would declare a `node` archetype, attach a typed `edge`
archetype, and spawn a walker that visits reachable nodes while deduping on
`jid`. But all of that is absent here.
