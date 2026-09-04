# Local Agent Office — 项目方案

> 面向 Codex 的长期项目总纲  
> 项目目标：将本地 Ubuntu 中某个代码仓库里的 AI Agents 运行状态，以 2D 办公室动画的方式实时可视化。

---

# 1. 项目概述

## 1.1 项目名称

**Local Agent Office**

这是一个运行在本地 Ubuntu 环境中的 Web 应用。

应用监听指定项目仓库中的 AI Agent 运行情况，并将 Agent 映射为一个 2D 办公室中的“虚拟员工”。

每一个真实运行中的 Agent，对应办公室中的一个员工角色。

Agent 的运行状态将映射为员工在办公室中的行为，例如：

- coding → 坐在工位敲代码
- thinking → 坐在工位思考
- tool_running → 起身前往工具区 / Server Room
- testing → 前往 Test Lab
- waiting → 在休息区等待
- idle → 去茶水间“摸鱼”
- error → 工位出现警告状态
- done → 完成任务后起身庆祝
- offline → 离开办公室

本项目首先服务于本地开发环境和个人使用，不以 SaaS、多租户或互联网部署为首要目标。

---

# 2. 核心设计理念

## 2.1 不是普通 Dashboard

本项目的重点不是：

```text
Agent A: Running
Agent B: Idle
Agent C: Error
```

而是：

```text
真实 Agent 状态
        ↓
Agent State Engine
        ↓
办公室空间行为
        ↓
角色动画
```

例如：

```text
Backend Agent
正在修改 backend/api.py
        ↓
状态 coding
        ↓
角色坐在 Desk B
        ↓
播放敲键盘动画
```

随后：

```text
Backend Agent
开始执行 pytest
        ↓
状态 testing
        ↓
角色站起来
        ↓
走到 Test Lab
        ↓
播放测试动画
```

因此，**状态变化本身必须驱动空间位置和动画行为。**

---

# 3. 总体架构

```text
┌──────────────────────────────┐
│ Ubuntu Project Repository    │
│                              │
│ Codex / Claude / Custom      │
│ Agents                       │
└──────────────┬───────────────┘
               │
               │ events / pid / git / fs
               ▼
┌──────────────────────────────┐
│ Agent Observer               │
│                              │
│ Process Observer             │
│ Git Observer                 │
│ Filesystem Observer          │
│ Agent Adapters               │
└──────────────┬───────────────┘
               │
               │ normalized events
               ▼
┌──────────────────────────────┐
│ Agent State Engine           │
│                              │
│ thinking                     │
│ coding                       │
│ testing                      │
│ tool_running                 │
│ waiting                      │
│ idle                         │
│ error                        │
│ done                         │
└──────────────┬───────────────┘
               │
               │ WebSocket
               ▼
┌──────────────────────────────┐
│ Frontend                     │
│                              │
│ React                        │
│ Zustand                      │
│ PixiJS                       │
│                              │
│ 2D Office Scene              │
└──────────────────────────────┘
```

---

# 4. 推荐技术栈

## 4.1 Backend

使用：

```text
Python 3.12+
FastAPI
Pydantic
WebSocket
psutil
GitPython
watchdog
```

职责：

- 管理项目仓库
- 监听 Agent
- 监听 Agent 生命周期
- 读取 Git 状态
- 读取文件修改
- 维护 Agent State
- 将状态变化通过 WebSocket 推送给前端

---

## 4.2 Frontend

使用：

```text
React
TypeScript
Vite
Zustand
PixiJS
@pixi/react（可选）
```

职责：

- WebSocket 连接
- Agent 状态管理
- 2D 办公室地图
- Agent Sprite
- 动画
- Agent 详情面板
- 调试 UI

---

## 4.3 不建议第一阶段使用

第一阶段不要引入：

```text
Next.js
Redux
PostgreSQL
Redis
Kafka
Docker Swarm
Kubernetes
Three.js
复杂 ECS
```

原因：

当前项目是本地单用户应用。

第一目标是：

```text
真实 Agent
    ↓
实时状态
    ↓
办公室动画
```

不要过度工程化。

---

# 5. 推荐项目目录

```text
agent-office/
│
├── backend/
│   │
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── agents.py
│   │   ├── projects.py
│   │   └── health.py
│   │
│   ├── observer/
│   │   ├── process.py
│   │   ├── git.py
│   │   ├── filesystem.py
│   │   └── manager.py
│   │
│   ├── adapters/
│   │   ├── base.py
│   │   ├── codex.py
│   │   ├── claude.py
│   │   └── custom.py
│   │
│   ├── state/
│   │   ├── agent.py
│   │   ├── event.py
│   │   ├── engine.py
│   │   └── registry.py
│   │
│   ├── websocket/
│   │   ├── manager.py
│   │   └── protocol.py
│   │
│   ├── runtime/
│   │   ├── events.py
│   │   └── storage.py
│   │
│   └── tests/
│
├── frontend/
│   │
│   ├── src/
│   │   │
│   │   ├── api/
│   │   │   └── websocket.ts
│   │   │
│   │   ├── store/
│   │   │   ├── agents.ts
│   │   │   └── office.ts
│   │   │
│   │   ├── office/
│   │   │   ├── OfficeScene.tsx
│   │   │   ├── AgentSprite.tsx
│   │   │   ├── Desk.tsx
│   │   │   ├── Zone.tsx
│   │   │   ├── Navigation.ts
│   │   │   └── animations.ts
│   │   │
│   │   ├── components/
│   │   │   ├── AgentPanel.tsx
│   │   │   ├── ProjectSelector.tsx
│   │   │   └── DebugPanel.tsx
│   │   │
│   │   ├── models/
│   │   │   └── agent.ts
│   │   │
│   │   └── App.tsx
│   │
│   └── package.json
│
├── config/
│   └── office.yaml
│
├── runtime/
│   └── events.jsonl
│
├── scripts/
│   └── office-run
│
├── AGENTS.md
├── PROJECT.md
├── README.md
└── .gitignore
```

---

# 6. 核心领域模型

## 6.1 Agent

Backend 统一数据模型：

```python
class AgentState(str, Enum):
    STARTING = "starting"
    THINKING = "thinking"
    CODING = "coding"
    TOOL_RUNNING = "tool_running"
    TESTING = "testing"
    SEARCHING = "searching"
    WAITING = "waiting"
    IDLE = "idle"
    ERROR = "error"
    DONE = "done"
    OFFLINE = "offline"
```

Agent：

```python
class Agent(BaseModel):
    id: str
    name: str

    provider: str

    pid: int | None

    repository: str
    worktree: str | None
    branch: str | None

    status: AgentState

    task: str | None

    current_tool: str | None

    changed_files: list[str]

    started_at: datetime
    last_active_at: datetime

    metadata: dict
```

---

# 7. Agent 状态映射

状态和办公室行为必须分离。

Backend 负责：

```text
Agent = CODING
```

Frontend 决定：

```text
CODING
    ↓
目标位置 = Assigned Desk
    ↓
角色行走到 Desk
    ↓
播放 typing animation
```

推荐映射：

| State | Office Zone | Animation |
|---|---|---|
| starting | entrance | entering |
| thinking | desk | thinking |
| coding | desk | typing |
| searching | library | reading |
| tool_running | tool_lab | working_machine |
| testing | test_lab | testing |
| waiting | lounge | waiting |
| idle | coffee_area | drinking |
| error | desk/tool_lab | error |
| done | desk | celebration |
| offline | exit | leaving |

---

# 8. Agent 生命周期

```text
Agent Process Start
        ↓
STARTING
        ↓
进入办公室
        ↓
THINKING
        ↓
CODING
        ↓
TOOL_RUNNING
        ↓
TESTING
        ↓
CODING
        ↓
DONE
        ↓
IDLE
        ↓
OFFLINE
        ↓
离开办公室
```

注意：

状态不保证线性。

例如：

```text
CODING → ERROR
TESTING → CODING
WAITING → TOOL_RUNNING
IDLE → THINKING
```

因此必须实现为状态机，而不是固定流程。

---

# 9. Agent Observer

Agent Observer 是整个项目最重要的 Backend 子系统。

Observer 负责将不同来源的数据转换为统一事件。

输入可能包括：

```text
Process
stdout
stderr
Git
Filesystem
Agent API
Wrapper
JSONL event
```

输出统一成：

```python
AgentEvent
```

---

# 10. AgentEvent

定义：

```python
class AgentEventType(str, Enum):
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"

    STATE_CHANGED = "agent.state_changed"

    TOOL_STARTED = "agent.tool_started"
    TOOL_FINISHED = "agent.tool_finished"

    FILE_CHANGED = "agent.file_changed"

    TASK_UPDATED = "agent.task_updated"

    ERROR = "agent.error"
```

示例：

```json
{
  "type": "agent.state_changed",
  "agent_id": "backend-agent",
  "timestamp": "2026-09-04T16:00:00+08:00",
  "payload": {
    "from": "coding",
    "to": "testing"
  }
}
```

---

# 11. Agent Adapter

必须定义抽象 Adapter。

```python
class AgentAdapter(ABC):

    @abstractmethod
    async def detect(self) -> list[Agent]:
        pass

    @abstractmethod
    async def observe(self, agent: Agent):
        pass
```

第一阶段至少支持：

```text
CodexAdapter
GenericProcessAdapter
```

后续：

```text
ClaudeAdapter
OpenCodeAdapter
CustomAgentAdapter
```

重要原则：

Frontend 永远不能依赖：

```text
Codex
Claude
OpenAI
```

Frontend 只应该理解：

```text
Agent
AgentState
AgentEvent
```

---

# 12. office-run Wrapper

长期推荐提供命令：

```bash
office-run codex --name backend-agent
```

而不是直接：

```bash
codex
```

Wrapper 做：

```text
1. 注册 Agent
2. 保存 Agent ID
3. 保存 PID
4. 保存 provider
5. 保存 repository
6. 启动真实 Codex
7. 捕获生命周期
8. 记录 exit
```

示例：

```bash
office-run codex \
    --name backend \
    --role Backend \
    --repo /home/louis/projects/my-project
```

生成：

```json
{
  "id": "backend",
  "name": "Backend",
  "provider": "codex",
  "pid": 18231,
  "repository": "/home/louis/projects/my-project"
}
```

---

# 13. 状态识别策略

不要只依赖 stdout 文本。

优先级建议：

```text
1. Agent 原生事件
2. Wrapper 事件
3. Process 信息
4. Git / filesystem activity
5. stdout heuristic
6. timeout heuristic
```

例如：

### coding

如果：

```text
检测到 repository 内文件修改
```

则：

```text
status = coding
```

### testing

如果 command 包含：

```text
pytest
npm test
pnpm test
cargo test
go test
mvn test
```

则：

```text
status = testing
```

### tool_running

如果 Agent 调用 shell / search / external tool：

```text
status = tool_running
```

### idle

例如：

```text
last_active > 30 seconds
```

则：

```text
status = idle
```

该时间必须配置化。

---

# 14. WebSocket 协议

连接：

```text
ws://localhost:8000/ws
```

初次连接：

```json
{
  "type": "snapshot",
  "agents": []
}
```

之后增量事件：

```json
{
  "type": "agent.started",
  "agent": {}
}
```

```json
{
  "type": "agent.updated",
  "agent_id": "backend",
  "changes": {
    "status": "coding"
  }
}
```

```json
{
  "type": "agent.stopped",
  "agent_id": "backend"
}
```

Frontend Store：

```text
WebSocket
    ↓
normalize
    ↓
Zustand
    ↓
Office Scene
```

---

# 15. Frontend 架构

Frontend 不应该把 PixiJS 和业务状态强耦合。

建议：

```text
Agent Store
    ↓
Agent Visual Controller
    ↓
Agent Sprite
```

例如：

```ts
agent.status === "testing"
```

Controller：

```ts
moveAgent("test_lab")
playAnimation("testing")
```

---

# 16. Office Scene

办公室至少包含：

```text
Entrance
Desk Area
Coffee Area
Lounge
Tool Lab
Test Lab
Library
Exit
```

V0 可以全部用占位图形。

不要一开始制作精美 Sprite。

示例：

```text
┌────────────────────────────────────┐
│ Entrance                           │
│                                    │
│ Desk A     Desk B      Desk C      │
│                                    │
│ Desk D     Desk E                  │
│                                    │
│ Coffee     Lounge      Library     │
│                                    │
│ Tool Lab               Test Lab    │
│                               Exit │
└────────────────────────────────────┘
```

---

# 17. Agent Sprite

Agent Sprite 状态：

```ts
type VisualState =
  | "idle"
  | "walking"
  | "typing"
  | "thinking"
  | "testing"
  | "tool"
  | "error"
  | "celebrating"
```

Agent Sprite 需要：

```text
position
targetPosition
currentAnimation
nameLabel
statusLabel
```

---

# 18. Pathfinding

V0：

使用简单 Tween。

```text
Agent current position
        ↓
target position
        ↓
linear interpolation
```

V1/V2：

如果办公室地图复杂：

```text
A*
```

但第一阶段不要实现 A*。

---

# 19. Agent 工位分配

需要实现 Desk Assignment。

规则：

```text
Agent 第一次进入办公室
        ↓
寻找 available desk
        ↓
assign
```

例如：

```ts
deskAssignments = {
    "backend": "desk-1",
    "frontend": "desk-2"
}
```

Agent 在：

```text
coding
thinking
error
```

时通常返回自己的 desk。

---

# 20. Agent Detail Panel

点击角色：

显示：

```text
Agent Name
Provider
Status
Task

PID
Branch
Worktree

Current Tool

Changed Files

Started At
Last Active

Recent Events
```

例如：

```text
Backend Agent

Status
Testing

Task
Implement authentication API

Branch
feat/auth

Changed Files
backend/api.py
backend/models.py

Current Tool
pytest

Recent Event
pytest tests/api
```

---

# 21. Project Selector

最终支持多个仓库。

例如：

```text
/home/louis/projects/quant_system
/home/louis/projects/robot
/home/louis/projects/agent-office
```

UI：

```text
Project:
[ robot ▼ ]
```

第一版可以只配置：

```yaml
project:
  path: /home/user/projects/demo
```

---

# 22. config/office.yaml

示例：

```yaml
project:
  name: demo
  path: /home/user/projects/demo

observer:
  idle_timeout: 30
  scan_interval: 1

server:
  host: 127.0.0.1
  port: 8000

office:
  desks: 8

frontend:
  port: 5173
```

---

# 23. Runtime Event Log

所有事件写：

```text
runtime/events.jsonl
```

示例：

```json
{"timestamp":"...","type":"agent.started","agent_id":"backend"}
{"timestamp":"...","type":"agent.state_changed","agent_id":"backend","from":"thinking","to":"coding"}
{"timestamp":"...","type":"agent.file_changed","agent_id":"backend","file":"backend/api.py"}
```

用途：

```text
debug
history replay
analytics
```

不要第一阶段引入数据库。

---

# 24. 开发阶段

---

# V0 — Office Simulator

目标：

完全不连接真实 Agent。

只开发：

```text
Frontend
Office Scene
Agent Sprite
State transitions
Animation
Fake WebSocket/Event simulator
```

必须实现：

- 2D Office
- 至少 5 个 Desk
- Coffee Area
- Tool Lab
- Test Lab
- Lounge
- 3~5 个模拟 Agent
- 不同状态动画
- 点击 Agent 查看详情
- 模拟状态变化
- Agent 可以移动

验收：

```text
状态改变
    ↓
位置改变
    ↓
动画改变
```

必须完整工作。

---

# V1 — Backend 基础

实现 FastAPI：

```text
GET /health
GET /api/agents
GET /api/project
WS /ws
```

实现：

```text
Agent Registry
State Engine
Event Bus
WebSocket Manager
```

Frontend 从 Fake Data 切换为 Backend。

验收：

Backend 产生：

```json
{
  "agent_id": "test-agent",
  "status": "testing"
}
```

Frontend Agent 自动移动到 Test Lab。

---

# V2 — Process + Git Observer

Backend 读取真实 Ubuntu 数据。

实现：

```text
psutil
GitPython
watchdog
```

能够发现：

```text
repository branch
modified files
process pid
process lifetime
```

验收：

仓库文件修改：

```text
backend/api.py
```

UI Agent Detail 能实时出现：

```text
Modified:
backend/api.py
```

---

# V3 — office-run + Codex

实现：

```bash
office-run codex
```

例如：

```bash
office-run codex --name backend
```

行为：

```text
启动 Codex
        ↓
注册 Agent
        ↓
Agent 进入办公室
```

Codex 退出：

```text
Agent OFFLINE
        ↓
角色走向 Exit
        ↓
从 Scene 移除
```

这是项目第一个真正重要的 Milestone。

---

# V4 — Agent Tool Detection

识别：

```text
shell
pytest
git
search
build
lint
```

映射：

```text
pytest → Test Lab
shell → Tool Lab
search → Library
```

---

# V5 — History Replay

利用：

```text
runtime/events.jsonl
```

支持：

```text
Replay
Pause
Speed 1x
Speed 2x
Speed 5x
```

可以回放 Agent 一段时间内的工作过程。

---

# V6 — Multiple Agents / Worktrees

支持：

```text
Codex Agent A
Codex Agent B
Claude Agent
Custom Agent
```

每个 Agent 可拥有：

```text
branch
worktree
task
role
```

办公室人数必须和 Active Agent 数同步。

---

# V7 — Advanced Office

可选：

```text
A* Pathfinding
Sprite Sheet
Pixel Art
Office Decoration
Weather / Time
Day Night Cycle
Achievements
Agent Personality
```

这些全部属于后续视觉层。

不得影响 Backend Domain Model。

---

# 25. API 设计

## GET /api/agents

返回：

```json
[
  {
    "id": "backend",
    "name": "Backend",
    "status": "coding"
  }
]
```

---

## GET /api/agents/{id}

返回完整 Agent。

---

## GET /api/project

返回：

```json
{
  "name": "robot",
  "path": "/home/user/projects/robot",
  "branch": "main"
}
```

---

## GET /health

```json
{
  "status": "ok"
}
```

---

# 26. Debug Mode

必须开发 Debug Panel。

开发期间能够人工修改状态：

```text
Backend
[ CODING ▼ ]

Planner
[ THINKING ▼ ]
```

按钮：

```text
Spawn Agent
Remove Agent
Randomize States
Generate Error
Reset
```

这样 Frontend 不依赖真实 Codex 就能开发。

---

# 27. 错误处理

WebSocket 断开：

```text
Frontend 自动 reconnect
```

状态：

```text
Connected
Reconnecting
Disconnected
```

Backend observer 出错：

不得导致服务器退出。

例如：

```python
try:
    ...
except Exception:
    logger.exception(...)
```

---

# 28. 日志

Backend 使用 Python logging。

建议：

```text
INFO
agent started

INFO
agent backend state changed coding → testing

DEBUG
file changed backend/api.py

ERROR
adapter failure
```

不要使用 print 作为正式日志方案。

---

# 29. Testing

Backend：

```text
pytest
```

重点测试：

```text
State Engine
Agent Registry
WebSocket serialization
Adapter normalization
```

Frontend：

可以使用：

```text
Vitest
```

重点：

```text
store event reducer
state → visual action mapping
```

不要求第一阶段进行复杂 UI 测试。

---

# 30. 代码规范

## Python

```text
type hints
async / await
Pydantic
dataclass where appropriate
small modules
```

不要：

```text
巨大 main.py
全局 mutable state
```

---

## TypeScript

开启 strict。

禁止大量：

```ts
any
```

核心模型必须定义 interface / type。

---

# 31. Codex 开发规则

Codex 实现本项目时必须遵守以下原则。

## 31.1 每次只实现当前阶段

例如当前任务：

```text
V0
```

则不要主动实现：

```text
Git Observer
Codex Adapter
History Replay
```

---

## 31.2 每个阶段完成后

必须：

```text
1. 运行测试
2. 运行 lint
3. 检查 build
4. 输出变更摘要
5. 输出下一阶段建议
```

---

## 31.3 不允许破坏 Domain Model

Frontend 不应该出现：

```ts
if (provider === "codex") ...
```

状态必须从 Backend 统一。

---

## 31.4 优先可运行

每个阶段必须保持：

```text
npm run dev
```

以及：

```text
uvicorn backend.main:app
```

能够成功启动。

---

## 31.5 不追求过度抽象

如果一个抽象只被调用一次：

不要为了“架构漂亮”而构造复杂框架。

---

# 32. V0 第一阶段具体任务

Codex 收到本文件后，第一轮开发优先完成以下内容：

## Task 1

初始化仓库：

```text
backend/
frontend/
config/
runtime/
scripts/
```

---

## Task 2

初始化 Frontend：

```text
React
TypeScript
Vite
PixiJS
Zustand
```

---

## Task 3

实现 Agent Model：

```ts
Agent
AgentState
```

---

## Task 4

实现 Zustand Store。

支持：

```text
addAgent
removeAgent
updateAgent
setAgentStatus
```

---

## Task 5

实现 OfficeScene。

V0 使用简单几何图形。

---

## Task 6

实现 Zone：

```text
desk_area
coffee_area
tool_lab
test_lab
lounge
entrance
exit
```

---

## Task 7

实现 AgentSprite。

至少显示：

```text
avatar
name
status
```

---

## Task 8

实现移动。

状态变化：

```text
coding
```

Agent：

```text
moveTo(desk)
```

状态：

```text
idle
```

Agent：

```text
moveTo(coffee_area)
```

---

## Task 9

实现 Debug Panel。

能够：

```text
人工切换 Agent 状态
```

---

## Task 10

实现模拟事件。

每 5~10 秒随机改变 Agent 状态。

必须可以：

```text
Pause Simulation
```

---

# 33. V0 验收标准

启动：

```bash
cd frontend
npm install
npm run dev
```

打开：

```text
http://localhost:5173
```

必须看到：

```text
2D Office
```

至少 4 个 Agent。

点击 Agent：

出现 Detail Panel。

修改 Agent 状态：

```text
coding → testing
```

角色：

```text
Desk
 ↓
walking
 ↓
Test Lab
```

状态：

```text
testing
```

动画改变。

如果做到以上内容：

```text
V0 PASS
```

---

# 34. UI 风格

初版：

```text
轻量 Pixel Office
```

但不要花大量时间制作美术。

推荐：

```text
灰色 / 米色办公室
简单角色
极简桌椅
清晰 Zone
```

角色区分主要通过：

```text
name
role
small color variation
```

不要一开始制作复杂 Skin。

---

# 35. 长期产品方向

如果核心架构稳定，未来可以扩展：

```text
Agent Office
    ↓
Agent Company
```

例如：

```text
Repository = Department

Frontend Repo
Backend Repo
Infra Repo

不同 Repo = 不同 Office Room
```

甚至：

```text
Workspace
    ↓
Building
    ↓
Floor
    ↓
Repository
    ↓
Agent
```

但当前版本不要实现。

---

# 36. 成功标准

项目最终应该让用户在几秒内通过视觉理解：

```text
现在有几个 Agent？
谁在工作？
谁在测试？
谁卡住？
谁报错？
谁在等待？
谁已经完成？
```

而不需要阅读大量 terminal。

核心价值：

```text
Agent Runtime
      ↓
Spatial Visualization
      ↓
Human Understanding
```

---

# 37. 当前最高优先级

当前只关注：

```text
V0
↓
V1
↓
V2
↓
V3
```

也就是：

```text
Office Simulation
↓
Backend State
↓
Ubuntu Observer
↓
Real Codex Agent
```

完成 V3 后，再判断是否值得继续发展高级视觉系统。

---

# 38. Codex 第一次执行指令

Codex 第一次进入项目时：

1. 阅读本文件。
2. 如果存在 `AGENTS.md`，同时阅读 `AGENTS.md`。
3. 不要直接开始 V1/V2/V3。
4. 首先检查仓库当前状态。
5. 如果仓库为空，从 V0 初始化。
6. 输出一份简短实施计划。
7. 开始实现 V0。
8. V0 完成后执行 build / test。
9. 报告：
   - 新增文件
   - 架构
   - 启动方式
   - 已完成 V0 验收项目
   - 未完成事项
10. 不自动进入下一阶段，等待用户确认。

---

# 39. 项目原则总结

始终牢记：

```text
真实 Agent 是事实源。
State Engine 是统一语言。
Frontend 只是可视化投影。
```

不要把业务逻辑写进动画代码。

不要让 Frontend 猜 Agent 在干什么。

不要让某个特定 Agent Provider 污染核心模型。

保持：

```text
Agent Provider
      ↓
Adapter
      ↓
Agent Event
      ↓
Agent State
      ↓
WebSocket
      ↓
Office Animation
```

这是整个项目最重要的架构边界。
