// Kiểu cho File Manager (SPEC 07).

export interface AllowedFolder {
  id: string;
  path: string;
  label: string;
  created_at: string;
}

export interface FsEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  mtime: number;
  ctime?: number;
  mime: string | null;
  checksum?: string;
}

export interface ScanResult {
  path: string;
  entries: FsEntry[];
}

export interface ReadResult {
  encoding: "text" | "base64";
  content: string;
  size: number;
}
