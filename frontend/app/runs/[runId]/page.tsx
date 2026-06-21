import { CorrectionPage } from "@/components/correction/CorrectionPage";

type PageProps = {
  params: Promise<{ runId: string }>;
};

export default async function RunReviewPage({ params }: PageProps) {
  const { runId } = await params;
  return <CorrectionPage runId={Number(runId)} />;
}
