// 首页“纹样总目”的固定编号顺序，纹样库筛选与首页共用。
export const OTHER_MOTIF = '其他'

export const MOTIF_ORDER = [
  '龙纹',
  '凤纹',
  '花卉纹',
  '缠枝/卷草纹',
  '云纹',
  '几何纹',
  '文字纹',
  '人物纹',
  OTHER_MOTIF,
]

export const MOTIF_EN = {
  龙纹: 'DRAGON',
  凤纹: 'PHOENIX',
  花卉纹: 'FLORA',
  '缠枝/卷草纹': 'SCROLL',
  云纹: 'CLOUD',
  几何纹: 'GEOMETRY',
  文字纹: 'INSCRIPTION',
  人物纹: 'FIGURE',
  其他: 'OTHER',
}

export const MOTIF_IMAGE = {
  龙纹: '/categories/dragon.png',
  凤纹: '/categories/phoenix.png',
  花卉纹: '/categories/flora.png',
  '缠枝/卷草纹': '/categories/scroll.png',
  云纹: '/categories/cloud.png',
  几何纹: '/categories/geometry.png',
  文字纹: '/categories/inscription.png',
  人物纹: '/categories/figure.png',
  其他: '/categories/other.png',
}

export function motifDisplayLabel(label) {
  return label === OTHER_MOTIF ? '其他（未归类）' : label
}

export function enrichMotif(item) {
  return {
    ...item,
    en: item.en || MOTIF_EN[item.label] || '',
    image: item.image || MOTIF_IMAGE[item.label] || '',
  }
}

export function sortMotifs(items) {
  const order = new Map(MOTIF_ORDER.map((label, index) => [label, index]))
  return [...items].sort((a, b) => {
    const left = order.get(a.label) ?? 99
    const right = order.get(b.label) ?? 99
    if (left !== right) return left - right
    return (b.count || 0) - (a.count || 0)
  })
}
