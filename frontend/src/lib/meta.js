import { ref } from 'vue'
import { apiFetch } from './api'
import {
  sampleMotifIndex,
  sampleDynastyIndex,
  sampleCarrierIndex,
} from '../data/patterns'
import { enrichMotif, sortMotifs } from '../data/motifs'

const motifs = ref(sortMotifs(sampleMotifIndex.map(enrichMotif)))
const dynasties = ref(sampleDynastyIndex)
const carriers = ref(sampleCarrierIndex)
const metaConnected = ref(false)
let pending = null

export async function loadMeta() {
  if (pending) return pending
  pending = apiFetch('/api/meta')
    .then((data) => {
      motifs.value = sortMotifs(data.motifs.map(enrichMotif))
      dynasties.value = data.dynasties
      carriers.value = data.carriers
      metaConnected.value = true
    })
    .catch(() => {
      metaConnected.value = false
    })
    .finally(() => {
      pending = null
    })
  return pending
}

export function useMeta() {
  return { motifs, dynasties, carriers, metaConnected, loadMeta }
}
