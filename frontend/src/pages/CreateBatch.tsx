import { useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../api/client";
import { useCreateBatch } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { BatchForm } from "../components/forms/BatchForm";
import { useUiStore } from "../store/ui";

export function CreateBatch() {
  const { id = "" } = useParams();
  const create = useCreateBatch(id);
  const navigate = useNavigate();
  const push = useUiStore((s) => s.pushToast);

  return (
    <SectionPanel
      title="Tạo lô (Batch)"
      description="Nạp danh sách input — mỗi dòng tạo 1 job (SPEC 01 §6)."
      spec="SPEC 03 §3"
    >
      <BatchForm
        submitting={create.isPending}
        onSubmit={(values) =>
          create.mutate(values, {
            onSuccess: (batch) => {
              push("success", `Đã tạo lô ${batch.input_count} job`);
              navigate(`/batches/${batch.id}`);
            },
            onError: (e) => push("error", (e as ApiError).message),
          })
        }
      />
    </SectionPanel>
  );
}
