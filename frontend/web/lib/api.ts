const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type AudioRecordOut = {
  id: number;
  uuid: string;
  source_type: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: string;
  language_code: string | null;
  notes: string | null;
  created_at: string;
};

export type AudioListResponse = {
  items: AudioRecordOut[];
  total: number;
};

export async function getMyAudio(accessToken: string): Promise<AudioListResponse> {
  const response = await fetch(`${apiBaseUrl}/audio/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Audio request failed: ${response.status}`);
  }

  return response.json();
}
