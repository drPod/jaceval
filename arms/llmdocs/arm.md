# Jac Language Reference

# 1. TYPES
int float str bool bytes any; list[T] dict[K,V] set[T] tuple[T,...]; int|None for optionals (NOT int?)
`has x: int;` `has y: str = "default";` `-> ReturnType` for function returns
True/False capitalized (true/false pass syntax check but FAIL at runtime)
Non-default attributes MUST come before default attributes in same archetype
WRONG: `has x: int = 0; has y: str;` RIGHT: `has y: str; has x: int = 0;`

# 2. CONTROL
```jac
if x < 5 { print("low"); } elif x < 10 { print("mid"); } else { print("high"); }
for item in items { print(item); }
for i=0 to i<10 by i+=1 { stmt; }
for (i, x) in enumerate(items) { print(i, x); }
while n > 0 { n -= 1; }
```
Match/case: colon after case, NO braces per case.
```jac
match value {
    case 1: print("one");
    case 2 | 3: print("two or three");
    case x if x > 5: print(f"big: {x}");
    case _: print("other");
}
```
WRONG: `case 1 { stmt; }` WRONG: `case "hi": { stmt; }` RIGHT: `case "hi": stmt;` RIGHT: `case "hi": if True { stmt; }`
Try/except: `try { } except TypeError as e { } finally { }` (NOT catch)
No ternary `?:` -- use `result = ("yes") if cond else ("no");`
No `pass` keyword -- use `{}` or comment
`(a, b) = func();` parens required for tuple unpacking

# 3. FUNCTIONS
```jac
def greet(name: str) -> str { return f"Hello, {name}!"; }
def no_args -> int { return 42; }
```
Lambda expression: `lambda x: int -> int : x * 2;`
Lambda block (MUST return): `lambda x: int -> int { return x * 2; };`
Lambda multi-param: `lambda x: int, y: int -> int : x + y;`
Lambda as argument: `items.sort(key=lambda x: dict -> float : x["v"]);`
Lambda with assignment MUST use block: `lambda e: any -> None { val = e.target.value; }`
Empty lambda body: `lambda e: any -> None { 0; }` NOT `{}`
Pipe: `"hello" |> print;` `[3,1,2] |> sorted |> list |> print;`
`glob var: T = val;` at module level. Access by name in functions. WRONG: `glob counter;` inside function body.
Top-level: only declarations allowed. Executable statements MUST go inside `with entry { }` or a function body.
Docstrings go BEFORE declarations, not inside bodies. Never name abilities list/dict/str/int or other builtins.
f-strings: `f"Value: {x}"` (server-side only; cl{} uses string concatenation)

# 4. IMPORTS
```jac
import os;                            # Namespace import
import from math { sqrt, pi }         # Selective (NO semicolon after })
import from .sibling { helper }       # Relative import
include utils;                        # C-style merge into current scope
```
`include` = inlines code into current scope. `import` = Python-style namespace separation.
`__init__.jac` required for packages. WRONG: `include nodes;` RIGHT: `include mypackage.nodes;` (full dotted paths)
WRONG: `import from math, sqrt;` WRONG: `import:py from os { path }` (no import:py/import:jac)
`with entry { }` always runs when module loads. `with entry:__main__ { }` only when file executed directly.

# 5. ARCHETYPES
```jac
node Person { has name: str; has age: int = 0; }
edge Friend { has since: int = 2020; }
walker Greeter { has greeting: str = "Hello"; can greet with Root entry; }
obj Point { has x: float; has y: float; }
enum Status { PENDING, ACTIVE, DONE }
enum Color { RED = "red", GREEN = "green" }
```
Inheritance: `obj Child(Parent) { }` `walker W(BaseW) { }` `node Dog(Animal) { }`
`can` for abilities (with entry/exit); `def` for regular methods
Impl blocks: `impl Calculator.add(n: int) -> int { self.value += n; return self.value; }`
Postinit: `has f: T by postinit; def postinit { self.f = val; }`
Boolean NOT: `not x` (Python-style). WRONG: `!x` (JS `!` does NOT exist in Jac)
Reserved keywords: obj node walker edge enum can has -- NEVER use as variable names.
WRONG: `obj = json.loads(s);` RIGHT: `data = json.loads(s);`

# 6. ACCESS
`has:pub x: str;` or `has :pub x: str;` (both valid). Only `:pub :priv :protect`
`def:pub get_items -> list { }` `walker:pub W { }` `node:priv Secret { }`
`:pub` on walker = public endpoint (no auth). Without `:pub` = requires auth token.

# 7. GRAPH
```jac
a ++> b;                              # Untyped forward
a <++ b;                              # Untyped backward (b -> a)
a <++> b;                             # Bidirectional
a +>: Friend(since=2020) :+> b;       # Typed forward
a <+: Friend() :<+ b;                 # Typed backward
a del--> b;                           # Disconnect
```
```jac
people = [-->](?:Person);             # Type filter
adults = [-->](?:Person, age > 18);   # Type+attr filter
old = [-->](?age > 18);               # Attr only
friends = [->:Friend:since > 2020:->]; # Edge attr filter
neighbors = [city_a ->:Road:->];      # Variable node traversal
untyped = [node_var -->];             # Untyped from variable
fof = [root ->:Friend:->->:Friend:->]; # Chained typed
edges = [edge root -->];              # Get edge objects
```
Untyped returns list: `nodes = root ++> Person(); first = nodes[0];`
Walrus: `root +>: E() :+> (end := A(val=10));`
Always assign filter results to variable or use in expression -- never bare statement.
WRONG: `a ++> Edge() ++> b;` `[-->:E:]` `del a --> b;` `[-->:E1:->-->:E2:->]`
RIGHT: `a +>: Edge() :+> b;` `[->:E:->]` `a del--> b;` `[->:E1:->->:E2:->]`

# 8. ABILITIES
```jac
node Gateway {
    has name: str;
    can on_any with entry { print(f"entered {self.name}"); }
    can on_inspect with Inspector entry { if visitor.clearance < 5 { disengage; } }
    can on_multi with Admin | Inspector entry { print("authorized"); }
    can on_leave with Inspector exit { print("leaving"); }
}
```
`self` = current archetype; `here` = current node (in walker ability); `visitor` = the walker (in node ability)
Root type: `Root` (capital R) in event clauses. WRONG: `` can act with `root entry ``
Union: `can process with Walker1 | Walker2 entry { }`

# 9. WALKERS
```jac
walker Search {
    has target: str;
    has results: list = [];
    can start with Root entry { visit [-->]; }
    can check with Person entry {
        if here.name == self.target { report here; disengage; }
        self.results.append(here.name);
        visit [-->] else { print("dead end"); }
    }
    can finish with Root exit { report self.results; }
}
```
Spawn (BOTH valid): `root spawn Walker();` AND `Walker() spawn root;`
NEVER bare keyword: WRONG: `node spawn W();` RIGHT: `root spawn W();` or `my_var spawn W();`
`visit` QUEUES nodes for next step (NOT immediate). Code after visit continues.
`visit [-->];` `visit [->:Road:->];` `visit self.target;` `visit : 0 : [-->];` (first only)
`visit [-->] else { fallback; }` for dead ends
`report` appends to `.reports` array: `result = root spawn W(); data = result.reports[0];`
`disengage` immediately terminates walker. Exit abilities for ancestors will NOT execute (v0.9.8+).
`skip` skips remaining code in current node's ability, moves to next queued node.
DFS traversal: entries depth-first, exits LIFO. root->A->B: Enter root, Enter A, Enter B, Exit B, Exit A, Exit root.

# 10. BY_LLM
```jac
def classify(text: str) -> str by llm;
def categorize(title: str) -> Category by llm();
def summarize(text: str) -> str by llm(temperature=0.7, model_name="gpt-4");
# Inline
result = "Explain quantum computing" by llm;
```
No import needed for basic `by llm`. For Model config:
`import from byllm.lib { Model }` `glob llm = Model(model_name="gpt-4o-mini");`
Semstrings: `has desc: str = "" """hint for LLM""";` (default value required before hint)
Sem annotations: `sem Ingredient.cost = "Estimated cost in USD";`
Enum classification constrains LLM to valid values:
```jac
enum Sentiment { POSITIVE, NEGATIVE, NEUTRAL }
def analyze(text: str) -> Sentiment by llm();
# sem Sentiment.POSITIVE = "Expresses happiness or approval";
```
Structured output: `def extract(text: str) -> list[Product] by llm();`
Tools: `def answer(q: str) -> str by llm(tools=[get_weather, search_web]);`
Context: `def support(q: str) -> str by llm(incl_info={"ctx": company_info});`

# 11. FILE_JSON
```jac
with entry {
    with open("data.json") as f { data = f.read(); }
    import json;
    parsed = json.loads(data);
    output = json.dumps(parsed, indent=2);
}
```
WRONG: `obj = json.loads(s);` (obj is keyword) RIGHT: `data = json.loads(s);`

# 12. API
`jac start file.jac` (NOT `jac serve`). ALL walkers register at `POST /walker/<WalkerName>`.
`GET /walker/<Name>` returns metadata only (does NOT execute).
`__specs__` is VESTIGIAL in 0.10.2 -- methods, path, path_prefix are IGNORED by server.
`:pub` on walker = public (no auth). Without `:pub` = requires auth token.
Auth endpoints: `POST /user/register` and `POST /user/login`
`:pub` walker root access is READ-ONLY. Graph writes silently fail when here is root. Use built-in auth for write access.
Custom auth (OAuth/JWT): make ALL walkers `:pub`, handle auth manually inside walker body.
Walkers CANNOT access HTTP headers, query params, cookies, or request object. ALL data must be passed as walker `has` fields in POST body.
Non-default `has` fields are REQUIRED POST params. `has x: list;` without default = required. Use `has x: list = [];` if optional.
Union types `T | None = None` may cause 422 in jac-scale (pydantic). Use concrete defaults instead.
OAuth GET redirects cannot hit walker endpoints (POST-only). Redirect to frontend, then POST to walker.
Response format: `{"ok":true, "type":"response", "data":{"result":..., "reports":[...]}, "error":null, "meta":{...}}`
Client fetch: `response.data.reports[0]` for reported values.
SSO routes (`/sso/{platform}/{operation}`) and OpenAPI (`/docs`) available ONLY with jac-scale plugin.

# 13. WEBSOCKET
```jac
async walker :pub Echo {
    async can echo with Root entry { report here; }
}
```
Connect: `ws://host/walker/Echo`. Remove `:pub` for authenticated websocket.
`socket.notify_users(ids, msg);` `socket.notify_channels(names, msg);` `broadcast=True` for broadcasting.

# 14. WEBHOOKS
```jac
walker :pub WebhookHandler {
    obj __specs__ {
        static has webhook: dict = {"type": "header", "name": "X-Signature"};
    }
    can handle with Root entry { report "received"; }
}
```

# 15. SCHEDULER
```jac
walker :pub DailyTask {
    obj __specs__ {
        static has schedule: dict = {"trigger": "cron", "hour": "9"};
        static has private: bool = True;
    }
    can run with Root entry { report "done"; }
}
```
Triggers: cron, interval, date.

# 16. ASYNC
```jac
async walker Crawler { async can crawl with Root entry { visit [-->]; } }
import from time { sleep }
def slow(n: int) -> int { sleep(1); return n * 2; }
with entry {
    t1 = flow slow(1); t2 = flow slow(2);
    print(wait t1, wait t2);
}
```
`flow` launches background task (thread pool), returns future. `wait` retrieves result (blocks if needed).
`flow/wait` = CPU-bound parallel. `async/await` = I/O-bound event loop.
Task status: `task.__jac__.status;` `task.__jac__.reports;` `task.__jac__.error;`

# 17. PERMISSIONS
`node.__jac__.grant(root, WritePerm);` `node.__jac__.revoke(root, WritePerm);`
Levels: NoPerm ReadPerm ConnectPerm WritePerm

# 18. PERSISTENCE
Nodes connected to root auto-persist. `save(node);` `commit();` `&id` for reference. `del node; commit();`

# 19. TESTING
```jac
test { assert 1 + 1 == 2; }
test {
    root ++> Person(name="Alice", age=30);
    result = root spawn Greeter();
    assert len(result.reports) > 0;
}
```
0.10.2: no test names. WRONG: `test "name" { }` WRONG: `test my_test { }`

# 20. STDLIB
Builtins: print len range type isinstance str int float list dict set tuple sorted enumerate zip map filter sum min max abs round any all
String: .upper() .lower() .strip() .split() .join() .replace() .startswith() .endswith() .find() f"..."
List: .append() .extend() .pop() .insert() .remove() .sort() .reverse() [i:j] comprehensions
Dict: .keys() .values() .items() .get(k, default) .update() .pop(k) comprehensions

# 21. JSX/CLIENT
TWO approaches: (1) `.cl.jac` files = entire file is client-side (no cl{} wrapper). (2) `cl{}` blocks inside `.jac` files = mixed server+client.
`.cl.jac` auto-compiled to JS. Do NOT include via `include`.
```jac
cl import from react { useState, useEffect }
sv import from __main__ { GetCount, Increment }
cl {
    def:pub app() -> JsxElement {
        has count: int = 0;
        has loading: bool = True;
        async can with entry {
            result = root spawn GetCount();
            if result.reports { count = result.reports[0]; }
            loading = False;
        }
        return <div>
            <p>Count: {count}</p>
            <button onClick={lambda e: any -> None { 0; }}>Click</button>
        </div>;
    }
}
```
`has` in client components = React useState (reactive state).
`root spawn` in cl{} compiles to `await` + POST to `/walker/<Name>`. Function MUST be `async def`.
Lifecycle: `useEffect(lambda -> None { func(); }, []);` NOT `can with entry`
JSX comprehensions: `{[<li>{item}</li> for item in items]}` compiles to `.map()`. Filter: `{[<li>{x}</li> for x in items if x.active]}`
Component return type: `-> JsxElement` (NOT `-> any` which conflicts with builtin)
CSS: `import "./styles.css";` or `import '.styles.css';`
cl{} JS builtins: `.length` not `len()`; `String(x)` not `str(x)`; `parseInt(x)` not `int(x)`; `Math.min/max`; `.trim()` not `.strip()`; no `range()`; no f-strings (use `+`); no tuple unpacking; `className` not `class`
`new` keyword does NOT exist. WRONG: `new Date()`. RIGHT: `Reflect.construct(Date, [val])`
`None` compiles to `null` in cl{} context. Use `None` in Jac source.
`cl import` / `sv import` prefixes at TOP LEVEL (outside cl{} block) for cross-context imports.
`.jac/` auto-generated, never modify manually.

# 22. CLIENT_AUTH
```jac
cl import from "@jac/runtime" { jacSignup, jacLogin, jacLogout, jacIsLoggedIn }
```
Per-user graph isolation with built-in auth.

# 23. JAC.TOML
```toml
[project]
name = "myapp"
entry-point = "main.jac"
[dependencies]
python-dotenv = ">=1.0.0"
[dependencies.npm]
tailwindcss = "^4.0.0"
"@tailwindcss/postcss" = "^4.0.0"
[dependencies.npm.dev]
"@jac-client/dev-deps" = "1.0.0"
[serve]
base_route_app = "app"
port = 8000
[plugins.client]
port = 5173
```
npm deps: ALL in jac.toml. NEVER `npm install` in `.jac/client/`.
Tailwind v4: `tailwindcss` + `@tailwindcss/postcss` in `[dependencies.npm]`.

# 24. FULLSTACK_SETUP
`jac create --use client` (NOT `--use fullstack`). `jac install` syncs all deps. `jac add --npm pkgname`.
Project structure: `main.jac` `__init__.jac` `jac.toml` `.jac/` (auto-gen)
`__init__.jac`: use full dotted paths. WRONG: `include nodes;` RIGHT: `include mypackage.nodes;`

# 25. DEV_SERVER
`jac start --dev` for hot reload. `--port` = Vite frontend (8000). `--api_port` = backend (8001, auto-proxied).
Proxy routes: `/walker/*` `/function/*` `/user/*` forwarded to backend.
`jac start --no-client` for backend-only.

# 26. DEPLOY_ENV
```dockerfile
FROM python:3.11-slim
RUN pip install jaseci
COPY . /app
WORKDIR /app
CMD ["jac", "start", "main.jac"]
```
`jaseci` = full runtime (persistence/auth plugins). `jaclang` = compiler-only.
`jac start --scale` for production (no `-t` flag).
Env vars: `DATABASE_URL` `JAC_SECRET_KEY` `OPENAI_API_KEY`
.env not auto-loaded:
```jac
import from dotenv { load_dotenv }
import from os { getenv }
glob _: bool = load_dotenv() or True;
```

# PATTERN 1: Fullstack Counter (single-file with cl{} block)
```jac
# main.jac
node Counter { has count: int = 0; }

walker :pub GetCount {
    can get with Root entry {
        counters = [-->](?:Counter);
        if counters { report counters[0].count; }
        else { report 0; }
    }
}

walker :pub Increment {
    can inc with Root entry {
        counters = [-->](?:Counter);
        if counters { counters[0].count += 1; report counters[0].count; }
    }
}

with entry {
    root ++> Counter(count=0);
}

cl import from react { useEffect }
sv import from __main__ { GetCount, Increment }

cl {
    def:pub app() -> JsxElement {
        has count: int = 0;
        has loading: bool = True;

        async can with entry {
            result = root spawn GetCount();
            if result.reports { count = result.reports[0]; }
            loading = False;
        }

        async def do_increment() -> None {
            result = root spawn Increment();
            if result.reports { count = result.reports[0]; }
        }

        if loading { return <p>Loading...</p>; }
        return <div>
            <h1>Count: {count}</h1>
            <button onClick={lambda e: any -> None { do_increment(); }}>+1</button>
        </div>;
    }
}
```
```toml
# jac.toml
[project]
name = "counter"
entry-point = "main.jac"
[serve]
base_route_app = "app"
```

# PATTERN 2: Walker Graph Traversal (Cities/Roads)
```jac
node City { has name: str; has visited: bool = False; }
edge Road { has distance: float; has toll: bool = False; }

walker FindReachable {
    has reachable: list = [];
    can start with Root entry { visit [-->]; }
    can explore with City entry {
        if not here.visited {
            here.visited = True;
            self.reachable.append(here.name);
            visit [->:Road:->];
        }
    }
    can finish with Root exit { report self.reachable; }
}

walker DeleteRoute {
    has from_city: str;
    has to_city: str;
    can start with Root entry { visit [-->]; }
    can find with City entry {
        if here.name == self.from_city {
            targets = [here ->:Road:->](?:City, name == self.to_city);
            for t in targets { here del--> t; }
            report f"Deleted route {self.from_city} -> {self.to_city}";
            disengage;
        }
        visit [->:Road:->];
    }
}

with entry {
    nyc = City(name="NYC");
    bos = City(name="Boston");
    dc = City(name="DC");
    root ++> nyc;
    nyc +>: Road(distance=215.0, toll=True) :+> bos;
    nyc +>: Road(distance=225.0, toll=False) :+> dc;
    bos +>: Road(distance=440.0, toll=True) :+> dc;

    # Variable node traversal + edge attr filter
    toll_roads = [nyc ->:Road:toll == True:->];
    print("Toll destinations from NYC:", [c.name for c in toll_roads]);

    result = root spawn FindReachable();
    print("Reachable:", result.reports[0]);

    result2 = root spawn DeleteRoute(from_city="NYC", to_city="DC");
    print(result2.reports[0]);
}
```

# PATTERN 3: API Todo CRUD
```jac
node Todo { has title: str; has done: bool = False; has priority: str = "medium"; }

walker :pub ListTodos {
    can list with Root entry {
        todos = [-->](?:Todo);
        report [{"title": t.title, "done": t.done, "priority": t.priority} for t in todos];
    }
}

walker :pub AddTodo {
    has title: str;
    has priority: str = "medium";
    can add with Root entry {
        new_nodes = root ++> Todo(title=self.title, priority=self.priority);
        t = new_nodes[0];
        report {"title": t.title, "priority": t.priority};
    }
}

walker :pub FilterTodos {
    has filter_by: str = "all";
    can filter with Root entry {
        todos = [-->](?:Todo);
        results: list = [];
        match self.filter_by {
            case "high": results = [t for t in todos if t.priority == "high"];
            case "done": results = [t for t in todos if t.done];
            case "pending": results = [t for t in todos if not t.done];
            case _: results = todos;
        }
        report [{"title": t.title, "done": t.done, "priority": t.priority} for t in results];
    }
}

with entry { root ++> Todo(title="Setup Jac", priority="high"); }
```
Client fetch pattern:
```javascript
// All walkers: POST /walker/<Name>
fetch("/walker/ListTodos", {method:"POST", headers:{"Content-Type":"application/json"}, body:"{}"})
  .then(r => r.json()).then(d => d.data.reports[0]);
// AddTodo with required field
fetch("/walker/AddTodo", {method:"POST", headers:{"Content-Type":"application/json"},
  body: JSON.stringify({title:"New task", priority:"high"})})
  .then(r => r.json()).then(d => d.data.reports[0]);
```

# COMMON ERRORS
WRONG: `true/false` -> RIGHT: `True/False`
WRONG: `entry { }` -> RIGHT: `with entry { }`
WRONG: `import from math, sqrt;` -> RIGHT: `import from math { sqrt }`
WRONG: `import:py from os { path }` -> RIGHT: `import from os { path }`
WRONG: `node spawn W();` -> RIGHT: `root spawn W();` (node is keyword)
WRONG: `a ++> Edge() ++> b;` -> RIGHT: `a +>: Edge() :+> b;`
WRONG: `[-->:E:]` -> RIGHT: `[->:E:->]`
WRONG: `[-->:E1:->-->:E2:->]` -> RIGHT: `[->:E1:->->:E2:->]`
WRONG: `del a --> b;` -> RIGHT: `a del--> b;`
WRONG: `` (`?Type) `` -> RIGHT: `(?:Type)`
WRONG: `` (`?Type:attr>v) `` -> RIGHT: `(?:Type, attr > v)`
WRONG: `` can act with `root entry `` -> RIGHT: `can act with Root entry`
WRONG: `test "name" { }` -> RIGHT: `test { }`
WRONG: `test my_test { }` -> RIGHT: `test { }`
WRONG: `obj = json.loads(s);` -> RIGHT: `data = json.loads(s);`
WRONG: `str?` -> RIGHT: `str | None`
WRONG: `jac serve file.jac` -> RIGHT: `jac start file.jac`
WRONG: `jac create --use fullstack` -> RIGHT: `jac create --use client`
WRONG: `static has auth: bool = False;` -> RIGHT: `walker :pub W { }`
WRONG: `<div class="x">` -> RIGHT: `<div className="x">`
WRONG: `len(items)` in cl{} -> RIGHT: `items.length`
WRONG: `str(x)` in cl{} -> RIGHT: `String(x)`
WRONG: `f"Hello {x}"` in cl{} -> RIGHT: `"Hello " + x`
WRONG: `items = items + [x]` in cl{} -> RIGHT: `items.append(x)`
WRONG: `lambda e: any -> None {}` -> RIGHT: `lambda e: any -> None { 0; }`
WRONG: `include nodes;` in __init__.jac -> RIGHT: `include mypackage.nodes;`
WRONG: `npm install` in .jac/client/ -> RIGHT: `jac add --npm pkgname`
WRONG: `print("x");` at top level -> RIGHT: `with entry { print("x"); }`
WRONG: `case 1 { stmt; }` -> RIGHT: `case 1: stmt;`
WRONG: `case "hi": { stmt; }` -> RIGHT: `case "hi": if True { stmt; }`
WRONG: `catch Error as e { }` -> RIGHT: `except Error as e { }`
WRONG: `x > 0 ? "y" : "n"` -> RIGHT: `("y") if x > 0 else ("n")`
WRONG: `has x: int = 0; has y: str;` -> RIGHT: `has y: str; has x: int = 0;`
WRONG: `glob counter;` inside function -> RIGHT: just use `counter` directly
WRONG: `result.returns[0]` -> RIGHT: `result.reports[0]`
WRONG: `.map(lambda x -> ...)` in JSX -> RIGHT: `{[<li>{x}</li> for x in items]}`
WRONG: `pass` -> RIGHT: `{}` or comment
WRONG: `!x` -> RIGHT: `not x`
WRONG: `__specs__ methods/path` -> RIGHT: ignored in 0.10.2; all walkers POST /walker/<Name>
WRONG: `new Date()` in cl{} -> RIGHT: `Reflect.construct(Date, [val])`
WRONG: `def:pub app() -> any` -> RIGHT: `def:pub app() -> JsxElement`
WRONG: `fetch("/api/todos")` -> RIGHT: `fetch("/walker/ListTodos", {method:"POST"})`
WRONG: `ExecutionContext.get()` -> RIGHT: pass data as walker `has` fields in POST body
WRONG: `has x: list;` (no default) -> RIGHT: `has x: list = [];` (non-default = required POST param)
WRONG: `GET /walker/Name` to execute -> RIGHT: `POST /walker/Name`
WRONG: OAuth redirect to `/walker/Callback` -> RIGHT: redirect to frontend, then POST to walker