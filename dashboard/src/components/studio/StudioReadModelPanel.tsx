import { useEffect, useState } from 'react'
import { Badge } from '../ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import {
  STUDIO_VIEW_SECTION_KEYS,
  loadStudioApplicationReadModel,
  type StudioApplicationReadModel,
  type StudioViewSectionKey,
} from '../../api/studioReadModel'

const SECTION_LABELS: Record<StudioViewSectionKey, string> = {
  authorityProvenance: 'Authority / provenance',
  profileResolution: 'Profile resolution',
  storyHierarchy: 'Story hierarchy',
  shotTrace: 'Shot trace',
  stateReference: 'State / reference',
  jobsQaRepair: 'Jobs / QA / repair',
  ambiguityRecovery: 'Ambiguity / recovery',
  evidenceStatus: 'Evidence status',
}

interface Props {
  projectId: string
}

export default function StudioReadModelPanel({ projectId }: Props) {
  const [loadState, setLoadState] = useState<{
    projectId: string
    model: StudioApplicationReadModel | null
    error: string | null
  }>({ projectId, model: null, error: null })

  useEffect(() => {
    let active = true
    loadStudioApplicationReadModel(projectId)
      .then(value => {
        if (active) setLoadState({ projectId, model: value, error: null })
      })
      .catch(reason => {
        if (active) {
          setLoadState({
            projectId,
            model: null,
            error: reason instanceof Error ? reason.message : 'Studio read model unavailable',
          })
        }
      })
    return () => { active = false }
  }, [projectId])

  const isCurrentProject = loadState.projectId === projectId
  const model = isCurrentProject ? loadState.model : null
  const error = isCurrentProject ? loadState.error : null

  if (error) {
    return (
      <Card className="py-4" style={{ borderColor: 'var(--red)' }}>
        <CardHeader>
          <CardTitle className="text-xs tracking-widest uppercase">Studio application view</CardTitle>
          <CardDescription>Canonical application read model is unavailable. No fallback is promoted to canonical authority.</CardDescription>
        </CardHeader>
        <CardContent>
          <span className="text-[11px]" style={{ color: 'var(--red)' }}>{error}</span>
        </CardContent>
      </Card>
    )
  }

  if (!model) {
    return <div className="text-xs" style={{ color: 'var(--muted)' }}>Loading Studio application view…</div>
  }

  const canonical = model.sourceKind === 'CANONICAL_APPLICATION'
  return (
    <Card className="py-4">
      <CardHeader>
        <CardTitle className="text-xs tracking-widest uppercase">Studio application view</CardTitle>
        <CardDescription>
          Typed, versioned presentation model. UI state is non-authoritative and never writes repository truth directly.
        </CardDescription>
        <div className="flex gap-2 pt-2">
          <Badge variant={canonical ? 'default' : 'outline'}>{model.sourceKind}</Badge>
          <Badge variant="outline">v{model.readModelVersion}</Badge>
          <Badge variant="outline">{model.project.workflowState}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {!canonical && (
          <div className="mb-4 rounded-md p-3 text-[11px]" style={{ border: '1px solid var(--yellow)', color: 'var(--yellow)' }}>
            Legacy web compatibility projection. It may inform UX, but it is not canonical Story/Shot/State/Profile authority.
          </div>
        )}
        <div className="mb-4 flex flex-col gap-1 text-[11px]">
          <span>{model.project.label}</span>
          <span style={{ color: 'var(--muted)' }}>Project: {model.project.projectId}</span>
          <span style={{ color: 'var(--muted)' }}>
            Active profile: {model.project.activeProfileRef
              ? `${model.project.activeProfileRef.logicalId}@${model.project.activeProfileRef.versionId}`
              : 'not available in this projection'}
          </span>
        </div>
        <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))' }}>
          {STUDIO_VIEW_SECTION_KEYS.map(key => {
            const section = model.sections[key]
            return (
              <div key={key} className="rounded-md p-3 flex flex-col gap-2" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] tracking-widest uppercase">{SECTION_LABELS[key]}</span>
                  <Badge variant="outline" className="ml-auto">{section.status}</Badge>
                </div>
                {section.items.length === 0 ? (
                  <span className="text-[10px]" style={{ color: 'var(--muted)' }}>No view items.</span>
                ) : section.items.slice(0, 4).map(item => (
                  <div key={item.id} className="flex flex-col gap-0.5 text-[10px]">
                    <div className="flex gap-2">
                      <span>{item.label}</span>
                      <span className="ml-auto" style={{ color: 'var(--muted)' }}>{item.state}</span>
                    </div>
                    <span style={{ color: 'var(--muted)' }}>
                      {item.canonicalRef
                        ? `${item.canonicalRef.logicalId}@${item.canonicalRef.versionId}`
                        : item.authority ?? 'presentation-only'}
                    </span>
                    {item.provenanceRefs.length > 0 && (
                      <span style={{ color: 'var(--muted)' }}>evidence: {item.provenanceRefs.join(', ')}</span>
                    )}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
