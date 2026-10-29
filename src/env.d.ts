interface ImportMetaEnv {
  /** '1' in the live build for bizcare.pk, empty in the preview build. */
  readonly BIZCARE_LIVE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
