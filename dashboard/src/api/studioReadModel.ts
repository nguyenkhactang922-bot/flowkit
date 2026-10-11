import { fetchAPI } from './client'
import type { Character, Project, Request, Video } from '../types'

export const STUDIO_VIEW_SECTION_KEYS = [
  'authorityProvenance',
  'profileResolution',
  'storyHierarchy',
  'shotTrace',
  'stateReference',
  'jobsQaRepair',
  'ambiguityRecovery',
  'evidenceStatus',
] as const

export type StudioViewSectionKey = (typeof STUDIO_VIEW_SECTION_KEYS)[number]
export type StudioReadModelSource = 'CANONICAL_APPLICATION' | 'LEGACY_COMPATIBILITY'
export type StudioSectionStatus = 'READY' | 'EMPTY' | 'BLOCKED'

export interface StudioCanonicalRef {
  logicalId: string
  versionId: string
}

export interface StudioViewItem {
  id: string
  kind: string
  label: string
  state: string
  canonicalRef: StudioCanonicalRef | null
  authority: string | null
  provenanceRefs: string[]
}

export interface StudioViewSection {
  status: StudioSectionStatus
  items: StudioViewItem[]
}

export interface StudioApplicationReadModel {
  readModelVersion: 1
  sourceKind: StudioReadModelSource
  project: {
    projectId: string
    label: string
    workflowState: string
    activeProfileRef: StudioCanonicalRef | null
  }
  sections: Record<StudioViewSectionKey, StudioViewSection>
}

interface StudioHostResponse {
  apiVersion: number
  requestId: string
  ok: boolean
  data: StudioApplicationReadModel | null
  error: { code: string; message: string } | null
}

declare global {
  interface Window {
    flowkitHost?: {
      studio?: {
        getApplicationReadModel(projectId: string): Promise<StudioHostResponse>
      }
    }
  }
}

function compatibilityItem(
  id: string,
  kind: string,
  label: string,
  state: string,
  provenanceRefs: string[] = [],
): StudioViewItem {
  return {
    id,
    kind,
    label,
    state,
    canonicalRef: null,
    authority: 'LEGACY_COMPATIBILITY_ONLY',
    provenanceRefs,
  }
}

function blockedCompatibilitySection(label: string): StudioViewSection {
  return {
    status: 'BLOCKED',
    items: [
      compatibilityItem(
        `legacy:${label}`,
        'legacy-compatibility-boundary',
        `${label} is unavailable from the canonical Studio application in web compatibility mode.`,
        'NON_CANONICAL',
      ),
    ],
  }
}

function validateCanonicalReadModel(value: StudioApplicationReadModel): StudioApplicationReadModel {
  if (
    !value ||
    value.readModelVersion !== 1 ||
    value.sourceKind !== 'CANONICAL_APPLICATION' ||
    !value.project ||
    !value.sections
  ) {
    throw new Error('Studio application read model failed canonical validation')
  }
  for (const key of STUDIO_VIEW_SECTION_KEYS) {
    const section = value.sections[key]
    if (!section || !['READY', 'EMPTY', 'BLOCKED'].includes(section.status) || !Array.isArray(section.items)) {
      throw new Error(`Studio application read model section ${key} is invalid`)
    }
  }
  return value
}

async function loadLegacyCompatibilityProjection(projectId: string): Promise<StudioApplicationReadModel> {
  const [project, videos, requests, characters] = await Promise.all([
    fetchAPI<Project>(`/api/projects/${projectId}`),
    fetchAPI<Video[]>(`/api/videos?project_id=${projectId}`),
    fetchAPI<Request[]>(`/api/requests?project_id=${projectId}`),
    fetchAPI<Character[]>(`/api/projects/${projectId}/characters`),
  ])

  const failedRequests = requests.filter(request => request.status === 'FAILED')
  const activeRequests = requests.filter(request => request.status === 'PENDING' || request.status === 'PROCESSING')

  return {
    readModelVersion: 1,
    sourceKind: 'LEGACY_COMPATIBILITY',
    project: {
      projectId: project.id,
      label: project.name,
      workflowState: project.status,
      activeProfileRef: null,
    },
    sections: {
      authorityProvenance: blockedCompatibilitySection('Authority / provenance'),
      profileResolution: blockedCompatibilitySection('Profile resolution'),
      storyHierarchy: {
        status: videos.length > 0 ? 'READY' : 'EMPTY',
        items: videos.map(video => compatibilityItem(
          `legacy-video:${video.id}`,
          'legacy-video-container',
          video.title,
          video.status,
          [`legacy-video:${video.id}`],
        )),
      },
      shotTrace: blockedCompatibilitySection('Canonical shot trace'),
      stateReference: {
        status: characters.length > 0 ? 'READY' : 'EMPTY',
        items: characters.map(character => compatibilityItem(
          `legacy-entity:${character.id}`,
          'legacy-reference-entity',
          character.name,
          character.media_id ? 'REFERENCE_AVAILABLE' : 'REFERENCE_MISSING',
          character.media_id ? [`legacy-media:${character.media_id}`] : [],
        )),
      },
      jobsQaRepair: {
        status: requests.length > 0 ? 'READY' : 'EMPTY',
        items: requests.slice(0, 50).map(request => compatibilityItem(
          `legacy-request:${request.id}`,
          'legacy-generation-request',
          request.type,
          request.status,
          request.request_id ? [`legacy-request-id:${request.request_id}`] : [],
        )),
      },
      ambiguityRecovery: {
        status: failedRequests.length > 0 ? 'READY' : activeRequests.length > 0 ? 'BLOCKED' : 'EMPTY',
        items: failedRequests.slice(0, 25).map(request => compatibilityItem(
          `legacy-failure:${request.id}`,
          'legacy-request-failure',
          request.error_message || `${request.type} failed`,
          'RECOVERY_REQUIRED',
          [`legacy-request:${request.id}`],
        )),
      },
      evidenceStatus: {
        status: requests.length > 0 ? 'READY' : 'EMPTY',
        items: [
          compatibilityItem(
            `legacy-evidence:${project.id}`,
            'legacy-operational-evidence',
            `${requests.length} operational requests observed; this is not canonical Studio evidence authority.`,
            failedRequests.length > 0 ? 'HAS_FAILURES' : 'OBSERVED',
            [],
          ),
        ],
      },
    },
  }
}

export async function loadStudioApplicationReadModel(projectId: string): Promise<StudioApplicationReadModel> {
  const host = window.flowkitHost?.studio
  if (host) {
    const response = await host.getApplicationReadModel(projectId)
    if (!response.ok || !response.data) {
      const code = response.error?.code ?? 'APPLICATION_READ_MODEL_UNAVAILABLE'
      throw new Error(`Studio read model unavailable (${code})`)
    }
    return validateCanonicalReadModel(response.data)
  }
  return loadLegacyCompatibilityProjection(projectId)
}
