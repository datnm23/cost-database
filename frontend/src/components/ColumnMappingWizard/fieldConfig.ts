import { SystemField } from './types'

export const SYSTEM_FIELDS: SystemField[] = [
  {
    key: 'work_code',
    label: 'Work Code',
    labelVi: 'Mã công việc',
    required: false,
    icon: 'CodeOutlined',
    keywords: ['mã', 'code', 'mã cv', 'mã hiệu', 'mh', 'item code', 'mã công việc'],
  },
  {
    key: 'description',
    label: 'Description',
    labelVi: 'Mô tả công việc',
    required: true,
    icon: 'FileTextOutlined',
    keywords: ['mô tả', 'diễn giải', 'description', 'nội dung', 'tên công việc', 'hạng mục', 'công việc'],
  },
  {
    key: 'unit',
    label: 'Unit',
    labelVi: 'Đơn vị tính',
    required: true,
    icon: 'ColumnWidthOutlined',
    keywords: ['đơn vị', 'đvt', 'dvt', 'unit', 'uom'],
  },
  {
    key: 'quantity',
    label: 'Quantity',
    labelVi: 'Khối lượng',
    required: false,
    icon: 'NumberOutlined',
    keywords: ['khối lượng', 'kl', 'số lượng', 'sl', 'quantity', 'qty'],
  },
  {
    key: 'unit_price',
    label: 'Unit Price',
    labelVi: 'Đơn giá',
    required: false,
    icon: 'DollarOutlined',
    keywords: ['đơn giá', 'đg', 'unit price', 'giá', 'rate', 'price'],
  },
  {
    key: 'amount',
    label: 'Amount',
    labelVi: 'Thành tiền',
    required: false,
    icon: 'CalculatorOutlined',
    keywords: ['thành tiền', 'tt', 'amount', 'total', 'tổng'],
  },
]
