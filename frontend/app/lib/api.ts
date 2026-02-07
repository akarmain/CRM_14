export interface Contact {
  id: number
  birth_date: string
  last_name: string
  first_name: string
  middle_name: string
  photo: string
  extra_fields: Record<string, unknown>
}

export const getContacts = async (): Promise<Contact[]> => {
  const config = useRuntimeConfig()
  const apiBase =
    (config.public.apiBase as string | undefined) ?? "http://localhost:8000"
  return await $fetch<Contact[]>(`${apiBase}/api/contacts`)
}
