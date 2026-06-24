"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { FileUp, Loader2, Trash2 } from "lucide-react";

import { DocumentViewer } from "@/components/correction/DocumentViewer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast-host";
import {
  deleteProject,
  formatRunTime,
  getReferenceDocument,
  pollProjectUntilReferencesReady,
  pollProjectUntilSettled,
  pollRunUntilComplete,
  rerunTarget,
  uploadReference,
  uploadTarget,
} from "@/lib/api";
import {
  EMPTY_REFERENCE_HINTS,
  TARGET_DOC_TYPES,
  TargetDocType,
  hintsToPayload,
} from "@/lib/constants";
import { formatRunFindingsSummary } from "@/lib/runSummary";
import type { AnalysisRunSummary, ProjectDetail, ReferenceDocumentSummary } from "@/lib/types";

type ProjectTileProps = {
  project: ProjectDetail;
  onRefresh: () => void;
  onDeleted: () => void;
};

function ReferenceStatusBadge({ status }: { status?: string }) {
  if (status === "processing") {
    return <Badge variant="warning">Processing</Badge>;
  }
  if (status === "failed") {
    return <Badge variant="destructive">Failed</Badge>;
  }
  return null;
}

function RunStatusBadge({ status }: { status: string }) {
  if (status === "processing") {
    return <Badge variant="warning">Processing</Badge>;
  }
  if (status === "failed") {
    return <Badge variant="destructive">Failed</Badge>;
  }
  return null;
}

export function ProjectTile({ project, onRefresh, onDeleted }: ProjectTileProps) {
  const { showToast } = useToast();
  const referenceInputRef = useRef<HTMLInputElement>(null);
  const targetInputRef = useRef<HTMLInputElement>(null);
  const rerunInputRef = useRef<HTMLInputElement>(null);
  const [uploadingReference, setUploadingReference] = useState(false);
  const [uploadingTarget, setUploadingTarget] = useState(false);
  const [targetDocType, setTargetDocType] = useState<TargetDocType>(TARGET_DOC_TYPES[0].value);
  const [previewRef, setPreviewRef] = useState<{ summary: ReferenceDocumentSummary; text: string } | null>(null);
  const [confirmRefUpload, setConfirmRefUpload] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [rerunRunId, setRerunRunId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  const hasTargets = project.runs.length > 0;
  const isBusy =
    uploadingReference ||
    uploadingTarget ||
    project.references.some((ref) => ref.status === "processing") ||
    project.runs.some((run) => run.status === "processing");

  useEffect(() => {
    if (!isBusy) {
      return;
    }
    const interval = window.setInterval(() => {
      onRefresh();
    }, 3000);
    return () => window.clearInterval(interval);
  }, [isBusy, onRefresh]);

  const startRunPolling = (runId: number, fileName: string, rerun = false) => {
    void pollRunUntilComplete(runId)
      .then((run) => {
        if (run.status === "completed") {
          showToast({
            title: rerun ? "Re-analysis complete" : "Analysis complete",
            description: `${run.name} is ready for review.`,
            actionLabel: "Review findings",
            onAction: () => {
              window.location.href = `/runs/${run.id}`;
            },
          });
        } else {
          showToast({
            title: rerun ? "Re-analysis failed" : "Analysis failed",
            description: run.error_message ?? `${fileName} could not be analyzed.`,
          });
        }
        onRefresh();
      })
      .catch((error) => {
        showToast({
          title: rerun ? "Re-analysis failed" : "Analysis failed",
          description: error instanceof Error ? error.message : "Unknown error",
        });
        onRefresh();
      });
  };

  const handleReferenceUploads = async (files: FileList) => {
    const fileList = Array.from(files);
    if (fileList.length === 0) {
      return;
    }

    setUploadingReference(true);
    const pendingRefIds: string[] = [];
    try {
      for (const file of fileList) {
        const response = await uploadReference(project.id, file, hintsToPayload(EMPTY_REFERENCE_HINTS));
        pendingRefIds.push(response.id);
        showToast({
          title: "Processing reference document",
          description: `${file.name} is being analyzed…`,
        });
        onRefresh();
      }

      void pollProjectUntilReferencesReady(project.id, pendingRefIds)
        .then(() => {
          if (hasTargets) {
            showToast({
              title: "Reference ready — re-linting targets",
              description: "Existing target documents are being re-analyzed with the updated references.",
            });
            return pollProjectUntilSettled(project.id);
          }
          showToast({
            title:
              pendingRefIds.length === 1
                ? "Reference ready"
                : `${pendingRefIds.length} references ready`,
            description: "Reference documents are ready for linting.",
          });
          return null;
        })
        .then(() => onRefresh())
        .catch((error) => {
          showToast({
            title: "Reference processing failed",
            description: error instanceof Error ? error.message : "Unknown error",
          });
          onRefresh();
        });
    } catch (error) {
      showToast({
        title: "Reference upload failed",
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setUploadingReference(false);
    }
  };

  const openReferenceFilePicker = () => {
    if (hasTargets) {
      setConfirmRefUpload(true);
      return;
    }
    referenceInputRef.current?.click();
  };

  const handleTargetUploads = async (files: FileList) => {
    const fileList = Array.from(files);
    if (fileList.length === 0) {
      return;
    }

    setUploadingTarget(true);
    try {
      for (const file of fileList) {
        const response = await uploadTarget(project.id, file, targetDocType, file.name);
        showToast({
          title: "Processing target document",
          description: `${file.name} is being analyzed…`,
        });
        onRefresh();
        startRunPolling(response.analysis_run_id, file.name);
      }
    } catch (error) {
      showToast({
        title: "Target upload failed",
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setUploadingTarget(false);
    }
  };

  const handleRerunUpload = async (files: FileList) => {
    const file = files[0];
    if (!file || rerunRunId === null) {
      return;
    }
    try {
      const response = await rerunTarget(project.id, rerunRunId, file, targetDocType);
      showToast({
        title: "Re-analyzing target",
        description: `${file.name} is being linted against current references…`,
      });
      onRefresh();
      startRunPolling(response.analysis_run_id, file.name, true);
    } catch (error) {
      showToast({
        title: "Re-analysis failed",
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setRerunRunId(null);
    }
  };

  const openReferencePreview = async (summary: ReferenceDocumentSummary) => {
    if (summary.status === "processing") {
      showToast({
        title: "Reference still processing",
        description: `${summary.filename} is not ready to preview yet.`,
      });
      return;
    }
    if (summary.status === "failed") {
      showToast({
        title: "Reference processing failed",
        description: summary.error_message ?? `${summary.filename} could not be processed.`,
      });
      return;
    }
    try {
      const detail = await getReferenceDocument(project.id, summary.id);
      setPreviewRef({ summary, text: detail.text });
    } catch (error) {
      showToast({
        title: "Could not load reference",
        description: error instanceof Error ? error.message : "Unknown error",
      });
    }
  };

  const handleDeleteProject = async () => {
    setDeleting(true);
    try {
      await deleteProject(project.id);
      showToast({ title: "Project deleted", description: project.name });
      onDeleted();
    } catch (error) {
      showToast({
        title: "Could not delete project",
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  const renderRunRow = (run: AnalysisRunSummary) => {
    const summaryText =
      run.status === "completed"
        ? formatRunFindingsSummary(run.findings_summary)
        : run.status === "processing"
          ? "Analysis in progress…"
          : run.error_message ?? "Analysis failed";

    return (
      <div key={run.id} className="rounded-md border px-3 py-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            {run.status === "completed" ? (
              <Link href={`/runs/${run.id}`} className="font-medium hover:underline">
                {run.name}
              </Link>
            ) : (
              <p className="font-medium">{run.name}</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">{formatRunTime(run.created_at)}</p>
            <p className="mt-2 text-sm text-muted-foreground">{summaryText}</p>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2">
            <RunStatusBadge status={run.status} />
            {run.status === "completed" && (
              <Button asChild size="sm" variant="default">
                <Link href={`/runs/${run.id}`}>Fix issues →</Link>
              </Button>
            )}
            {run.status === "completed" && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setRerunRunId(run.id);
                  rerunInputRef.current?.click();
                }}
              >
                Upload new version
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <CardTitle className="text-lg">{project.name}</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-destructive"
            disabled={deleting}
            onClick={() => setConfirmDelete(true)}
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            Delete
          </Button>
        </CardHeader>
        <CardContent className="space-y-5">
          <div>
            <p className="mb-2 text-sm font-medium">References</p>
            <ul className="space-y-1">
              {project.references.map((ref) => (
                <li key={ref.id}>
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-secondary"
                    onClick={() => void openReferencePreview(ref)}
                  >
                    <span className="truncate">{ref.filename}</span>
                    <ReferenceStatusBadge status={ref.status} />
                  </button>
                </li>
              ))}
              {project.references.length === 0 && (
                <li className="px-2 text-sm text-muted-foreground">No references yet</li>
              )}
            </ul>
            <input
              ref={referenceInputRef}
              type="file"
              accept=".txt,.md,.pdf"
              multiple
              className="hidden"
              onChange={(event) => {
                const files = event.target.files;
                if (files && files.length > 0) {
                  void handleReferenceUploads(files);
                }
                event.target.value = "";
              }}
            />
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              disabled={uploadingReference}
              onClick={openReferenceFilePicker}
            >
              {uploadingReference ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileUp className="h-4 w-4" />
              )}
              Add reference
            </Button>
          </div>

          <div>
            <p className="mb-2 text-sm font-medium">Target documents</p>
            <div className="space-y-2">
              {project.runs.map(renderRunRow)}
              {project.runs.length === 0 && (
                <p className="text-sm text-muted-foreground">No target documents yet</p>
              )}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <select
                value={targetDocType}
                onChange={(event) => setTargetDocType(event.target.value as TargetDocType)}
                className="h-9 rounded-md border bg-background px-3 text-sm"
              >
                {TARGET_DOC_TYPES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <input
                ref={targetInputRef}
                type="file"
                accept=".txt,.md,.pdf"
                multiple
                className="hidden"
                onChange={(event) => {
                  const files = event.target.files;
                  if (files && files.length > 0) {
                    void handleTargetUploads(files);
                  }
                  event.target.value = "";
                }}
              />
              <input
                ref={rerunInputRef}
                type="file"
                accept=".txt,.md,.pdf"
                className="hidden"
                onChange={(event) => {
                  const files = event.target.files;
                  if (files && files.length > 0) {
                    void handleRerunUpload(files);
                  }
                  event.target.value = "";
                }}
              />
              <Button disabled={uploadingTarget} onClick={() => targetInputRef.current?.click()}>
                {uploadingTarget ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileUp className="h-4 w-4" />
                )}
                Upload target
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={confirmRefUpload} onOpenChange={setConfirmRefUpload}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add reference to existing project?</DialogTitle>
            <DialogDescription>
              This project already has linted target documents. Adding a reference will re-run lint
              on those targets using the expanded reference set.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmRefUpload(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                setConfirmRefUpload(false);
                referenceInputRef.current?.click();
              }}
            >
              Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete project?</DialogTitle>
            <DialogDescription>
              This permanently removes {project.name}, all references, and all lint results.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={deleting} onClick={() => void handleDeleteProject()}>
              Delete project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={previewRef !== null} onOpenChange={(open) => !open && setPreviewRef(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{previewRef?.summary.filename}</DialogTitle>
            <DialogDescription>{previewRef?.summary.doc_type}</DialogDescription>
          </DialogHeader>
          {previewRef && (
            <DocumentViewer
              text={previewRef.text}
              filename={previewRef.summary.filename}
              highlights={[]}
              className="max-h-[60vh]"
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
