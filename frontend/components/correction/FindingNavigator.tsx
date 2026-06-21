"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { CorrectionFindingView } from "@/lib/types";
import { PRIORITY_LABELS } from "@/lib/types";

type FindingNavigatorProps = {
  finding: CorrectionFindingView;
  index: number;
  total: number;
  onPrevious: () => void;
  onNext: () => void;
};

export function FindingNavigator({
  finding,
  index,
  total,
  onPrevious,
  onNext,
}: FindingNavigatorProps) {
  return (
    <footer className="fixed bottom-0 left-0 right-0 z-40 border-t bg-card/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <Button variant="outline" size="sm" onClick={onPrevious} disabled={index <= 0}>
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>
        <div className="min-w-0 text-center">
          <p className="truncate text-sm font-medium">
            {PRIORITY_LABELS[finding.priority]} · {index + 1} of {total}
          </p>
          <p className="truncate text-xs text-muted-foreground">{finding.title}</p>
        </div>
        <Button variant="outline" size="sm" onClick={onNext} disabled={index >= total - 1}>
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </footer>
  );
}
