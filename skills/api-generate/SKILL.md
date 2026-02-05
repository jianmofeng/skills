---
name: api-generate
description: 根据上传的 swagger.json 规范与当前项目 src/api 目录（特别是类似 src/api/print 下 types 与 libs 的组织方式）自动分析并生成指定业务模块的 API 类型定义和请求方法。用户上传 swagger.json 并指定模块与路径前缀或标签时，使用本 Skill 来对照项目已有 API 写法输出对应的 TypeScript d.ts 类型命名空间和 http 请求函数。
---

# API Generate（基于 swagger.json 的接口生成）

## 使用场景

当用户在本项目中说出类似：

- “我会上传一个 swagger.json，帮我按项目里的 API 写法，生成某个模块的接口文件”
- 生成 XX模块的接口文件
- swagger地址是：https://xxx/swagger.json，帮我生成 XX 模块的接口方法和类型声明

时，你应主动启用本 Skill。

本项目使用 Vite + Vue3 + TS，API 调用约定主要参考 `src/api` 目录下现有模块（尤其是 `src/api/print`）的结构：

- 在 `types/xxx.d.ts` 中定义该模块的类型命名空间（如 `export namespace Print { ... }`）
- 在 `libs/xxx.ts` 中定义具体的 http 请求方法，使用统一的 `http` 客户端与 `BuildUrl` 工具

## 总体目标

**目标**：基于用户提供的 swagger.json（OpenAPI 规范），结合当前项目中 `src/api` 的组织方式，自动为指定业务模块产出：

- 对应的 TypeScript 类型声明文件（通常为 `types/<module>.d.ts`）
- 对应的 API 调用封装文件（通常为 `libs/<module>.ts`）

并保证：

- 命名风格、文件结构与现有模块（例如 `src/api/print`）保持一致
- 使用统一的 http 请求封装与 URL 构建工具
- 不引入多余的依赖或额外架构复杂度（遵循 KISS / YAGNI）

---

## 项目 API 写法约定（参考示例）

在阅读 swagger 与生成代码前，先回顾当前项目的 API 写法约定。

### 类型文件（参考 `src/api/print/types/print.d.ts`）

- 使用 `export namespace Xxx { ... }` 的命名空间形式聚合同一模块的类型：
  - 示例：`export namespace Print { ... }`
- 在命名空间内部：
  - 定义业务实体接口，例如 `SkuInfo`、`PrintRecord` 等
  - 定义接口返回结构，例如 `GetSkuListPageRes`、`GenerateRes`
- 字段均为显式类型（string / number / boolean / 数组等），尽量避免 `any`

### 请求文件（参考 `src/api/print/libs/print.ts`）

- 统一 `import http, { HttpResponse } from '@/api/http/index'`
- 统一 `import { BuildUrl } from '@/utils/request'`
- 引入当前模块类型命名空间，例如：
  - `import { Print } from '../types/print'`
- 每个 API 一个导出函数，命名遵循“动词 + 业务”的语义命名：
  - 如 `getSkuList`、`generateBatchCode`、`savePrintRecordList` 等
- 函数签名：
  - 入参通常为 `data: any`（如 swagger 信息充分，可以尝试推导为更具体的类型，但若不确定则保持 `any` 避免过拟合）
  - 返回值为 `http<HttpResponse<XXX>>`，其中 `XXX` 是对应的 TS 类型或 `boolean` / 基础类型
- URL 构造：
  - 使用 `BuildUrl.<SERVICE>('/path')` 形式（例如 `BuildUrl.LMS('/admin/printRecord/generate')`）
  - `<SERVICE>`（如 `LMS`）需要与项目中已有模式或用户提示一致；如 swagger 未提供，可让用户确认或采用与相关模块相同的前缀
- 需要特殊配置时（例如导出 blob、长超时时间）：
  - 通过 `responseType: 'blob'`、`timeout: xxx` 等补充字段实现

---

## 目录结构约定与自动生成

当用户希望**直接在项目中生成完整目录与文件**时，应遵循以下目录结构，并在得到用户同意后实际创建对应文件：

- 模块根目录（示例以 `print` 为例）：
  - `src/api/print/`
    - `types/`：存放本模块的类型声明文件
      - `print.d.ts`：包含 `export namespace Print { ... }`
    - `libs/`：存放本模块的请求封装文件
      - `print.ts`：包含所有与本模块相关的 http 方法

对于新模块，推荐的通用结构为：

- `src/api/<module>/types/<module>.d.ts`
- `src/api/<module>/libs/<module>.ts`

可选（视项目实际需要）：

- `src/api/<module>/index.ts` 用于统一导出本模块的 API 方法与类型，便于其他地方按模块入口导入。

生成目录结构时的行为约定：

- 如果用户只要求“给出代码”，则仅返回代码片段，不自动创建文件。
- 如果用户明确表示“帮我生成/创建文件”“直接落到项目里”，则：
  - 按上述目录结构检查并创建缺失的目录；
  - 在对应路径下创建或更新文件内容；
  - 在回复中简要列出本次新建/修改的文件相对路径。

---

## 工作流程

当用户请求基于 swagger.json 生成某个模块 API 时，遵循以下步骤：

### 步骤 0：检查 swagger.json 是否已提供

1. **如果用户尚未提供 swagger.json 文件、本地路径或可访问的 swagger JSON 地址（URL）**：
   - 明确告知用户：需要先上传 swagger.json 文件，或提供本地可读取的 JSON 路径，或提供一个可直接访问的 swagger JSON 地址（如 `https://xxx/swagger.json`），才能继续后续步骤。
   - 在用户上传或指定有效的文件路径/URL 之前，不要尝试解析或生成任何接口/类型，只做“提示上传或提供地址”的响应。
2. **如果用户已经上传或提供 swagger.json 路径或 URL**：
   - 记录该文件路径或 URL，并在后续步骤中统一使用该 JSON 内容进行解析。

### 步骤 1：理解用户需求

1. 从用户话语中提取关键信息：
   - 目标模块名称（如“打印模块”“批次管理”“工厂管理”等）
   - swagger 中的路径前缀、tag、或其他筛选条件（如 `/admin/printRecord/*`、Tag = `Print`）
   - 需要生成的内容范围：
     - 仅类型 (`types/*.d.ts`)？
     - 仅请求方法 (`libs/*.ts`)？
     - 还是两者都要（默认：两者都要）？
2. 若用户未明确模块命名或路径前缀：
   - 尝试根据 swagger 中 Tag / path 推断一个合理的模块名（如 `print`、`batchPrint`）
   - 将推断结果在回答中明示，便于用户调整

### 步骤 2：解析 swagger.json

1. 识别 swagger / OpenAPI 基本结构：
   - `paths`：每个 URL + method 描述
   - `tags`：模块或分组信息
   - `components.schemas` 或 `definitions`：可复用的对象模型
2. 针对目标模块的接口：
   - 可通过以下方式筛选：
     - 按 Tag（如接口 `tags` 中包含指定模块 Tag）
     - 按 path 前缀（例如都以 `/admin/printRecord` 开头）
   - 将所有匹配的接口整理为一个列表，记录：
     - method（GET/POST/PUT/DELETE/…）
     - full path（例如 `/admin/printRecord/getPrintRecordListPage`）
     - operationId（若存在）
     - 请求体 / query 参数结构
     - 响应体结构（成功响应）

### 步骤 3：设计 TypeScript 类型结构

1. 在类型文件中使用命名空间：
   - 例如模块名为 `print`，则使用 `export namespace Print { ... }`
2. 为每个重要的响应结构生成接口：
   - 例如分页列表结果 → `GetXXXPageRes`
   - 列表项实体 → `XXXItem` 或 `PrintRecord` 等
3. 命名规则：
   - 以业务含义为主，结合 swagger 中的 schema 名称与字段含义
   - 避免过长、过技术化的命名，保持简洁清晰
4. 对于 swagger 中复用的 schema：
   - 尝试直接映射成一个接口
   - 避免生成大量几乎相同的重复接口
5. 字段类型推断：
   - 根据 swagger 中的 `type`、`format`、`items` 等推断到 TS 类型
   - 若 swagger 信息缺失或明显不一致，保守使用 `any` 或 `unknown`，并在注释中说明原因

### 步骤 4：设计请求函数结构

1. 为每个接口设计一个函数：
   - 函数名优先使用 operationId 的简化版或语义化翻译（英文/拼音）：
     - 例：`getPrintRecordListPage` → `getPrintRecordList`
   - 若用户有命名偏好，应优先按照用户提供的命名来生成
2. 请求方法：
   - 按 swagger 中 method（GET/POST 等）设置 `method` 字段
3. URL：
   - 直接使用 swagger path 作为 `BuildUrl.<SERVICE>('<path>')` 的路径部分
   - `<SERVICE>` 前缀若未从项目中推断出，则：
     - 尽量复用与当前模块相关的已有 Service 名称
     - 或保留为 TODO 注释，提示用户补充
4. 入参：
   - 若 swagger 使用 `requestBody` schema，则将 body 作为 `data` 传入
   - 若只有 query / path 参数，可考虑统一封装为一个 `params` 或 `data` 对象
   - 若信息不充分，保留 `data: any` 以避免类型过于严格
5. 返回类型：
   - 根据 swagger 响应 schema，映射到前面生成的 TS 类型
   - 最终返回值统一为 `http<HttpResponse<XXX>>`

### 步骤 5：对齐现有模块风格

在生成前或生成过程中，务必对照本项目中已有模块（尤其是用户指定的示例，例如 `src/api/print`）：

- 对比导入路径、导出方式是否一致
- 对比命名是否符合全局约定（例如是否使用命名空间、是否大驼峰）
- 对比是否使用相同的 `http` 封装与 `BuildUrl` 工具

如发现与现有模块有冲突的地方，应优先保持与既有代码风格一致，而不是自创新风格。

---

## 输出格式约定

当用户请求生成代码时，回答时应尽量按照以下格式输出：

1. **简短说明**
   - 概括本次根据 swagger 生成了哪些模块、文件和函数
2. **类型文件内容（建议单独代码块）**
   - 如：`types/<module>.d.ts`
   - 使用命名空间包裹的接口声明
3. **请求文件内容（建议单独代码块）**
   - 如：`libs/<module>.ts`
   - 包含全部 API 调用函数
4. 如有需要用户确认或补充的信息（例如 Service 前缀、部分字段类型不确定），在说明中以列表形式清晰列出。

示例结构（伪代码）：

```markdown
### 1. 类型声明（types/xxx.d.ts）

```ts
export namespace Xxx {
  export interface Yyy { ... }
  export interface GetYyyListRes { ... }
}
```

### 2. 请求封装（libs/xxx.ts）

```ts
import http, { HttpResponse } from '@/api/http/index'
import { BuildUrl } from '@/utils/request'
import { Xxx } from '../types/xxx'

export function getYyyList(data: any) {
  return http<HttpResponse<Xxx.GetYyyListRes>>({
    method: 'POST',
    url: BuildUrl.LMS('/admin/yyy/getYyyListPage'),
    data,
  })
}
```
```

---

## 设计原则

在使用本 Skill 生成代码时，始终遵循以下工程原则：

- **DRY**：避免为同一业务结构生成多份重复类型或函数，优先复用命名空间内已有接口
- **KISS**：保持函数签名与类型结构简单清晰，避免过度抽象
- **SOLID**：每个函数只封装一个明确的后端接口；模块聚焦单一业务领域
- **YAGNI**：只生成用户当前需要的模块和接口，不预生成未请求的接口或工具函数

如有多种实现方式可选，优先选择与项目中现有 API 模块最接近、最简单的实现。

---

## 附加示例

需要查看一个完整的 types + libs 模块写法示例（基于现有 `src/api/print` 模块）时，请参考同目录下的 `examples.md`。

