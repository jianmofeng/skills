# api-generate 示例：基于 print 模块的完整用法

本文件根据示例文件生成结构，作为后续根据 swagger 生成代码时的对照范例，不再依赖项目内的文件。

---

## 1. 类型声明文件示例（`src/api/print/types/print.d.ts`）

```ts
export namespace Print {
  export interface SkuInfo {
    /*箱规数 */
    boxQty: number

    /*物料编码 */
    materialCode: string

    /*SKU编码 */
    skuCode: string

    /*业务主键ID */
    skuId: number

    /*SKU名称 */
    skuName: string

    /*SKU状态 */
    skuStatus: string

    /*SKU状态名称 */
    skuStatusName: string

    /*规格名称 */
    specName: string

    /*规格简码 */
    specSimpleCode: string

    /*商品编码 */
    spuCode: string
  }

  export interface GetSkuListPageRes {
    /* 列表数据 */
    data: SkuInfo[]
    /* 当前页码 */
    pageNo: number
    /* 每页数量 */
    pageSize: number
    /* 总页数 */
    pages: number
    /* 总条数 */
    total: number
  }
}
```

### 要点提炼

- 使用 `export namespace Print { ... }` 将同一业务模块（打印相关）下的所有类型聚合在一个命名空间中。
- 分离“列表项实体”（`SkuInfo`）与“接口返回结构”（`GetSkuListPageRes`）。
- 字段类型全部显式声明（string / number / boolean / array），避免 `any`。

---

## 2. 请求封装文件示例（`src/api/print/libs/print.ts`）

```ts
import http, { HttpResponse } from '@/api/http/index'
import { BuildUrl } from '@/utils/request'
import { Print } from '../types/print'

/** 获取SKU表列表(分页) */
export function getSkuList(data: any) {
  return http<HttpResponse<Print.GetSkuListPageRes>>({
    method: 'POST',
    url: BuildUrl.LMS('/xxxx/xxx/getList'),
    data,
  })
}

```

### 要点提炼

- **统一导入**：
  - `http, { HttpResponse }` 从 `@/api/http/index` 导入。
  - `BuildUrl` 从 `@/utils/request` 导入。
  - 当前模块类型命名空间从相对路径 `../types/print` 导入。
- **函数命名**：
  - 采用“动词 + 业务含义”的形式（`getSkuList`、`generateBatchCode`、`savePrintRecordList` 等），保持简短且语义清晰。
- **返回类型**：
  - 使用 `http<HttpResponse<XXX>>` 统一包裹后端返回，其中 `XXX` 为具体业务类型（如 `Print.GetSkuListPageRes`、`Print.GenerateRes` 或 `boolean`）。
- **URL 构造**：
  - 一致使用 `BuildUrl.LMS('/admin/xxx/yyy')` 形式，将路径前缀逻辑收敛到 `BuildUrl` 工具。
- **特殊配置**：
  - 导出文件时，通过 `responseType: 'blob'` 指定响应类型。
  - 长耗时操作通过 `timeout` 字段单独配置。

---

## 3. 作为 swagger 生成的参考规范

当基于 swagger.json 为新模块生成 API 时，应尽量遵循上述模式：

- 在 `types/<module>.d.ts` 中定义命名空间 + 业务类型；
- 在 `libs/<module>.ts` 中定义 http 请求函数，并：
  - 使用统一的导入方式；
  - 采用语义化函数命名；
  - 使用 `HttpResponse<业务类型>` 作为泛型返回值；
  - 使用 `BuildUrl.<SERVICE>` 包装后端路径；
  - 在需要的地方配置 `timeout` / `responseType` 等额外参数。

这可以保证自动生成的代码风格与现有手写模块（例如 `print`）保持一致，便于维护与扩展。

