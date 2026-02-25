export interface Contact {
  id: number
  first_name: string
  last_name: string
  middle_name?: string | null
  birth_date?: string | null
  avatar_url?: string | null
  extra_fields: Record<string, unknown>
}

export interface ContactCreate {
  first_name: string
  last_name: string
  middle_name?: string | null
  birth_date?: string | null
  avatar_url?: string | null
  extra_fields?: Record<string, unknown>
}

const apiBase = () => {
  const config = useRuntimeConfig()
  return (config.public.apiBase as string | undefined) ?? "http://localhost:8000"
}

export const getContacts = async (search?: string): Promise<Contact[]> => {
  return await $fetch<Contact[]>(`${apiBase()}/api/v1/contacts`, {
    query: search ? { search } : undefined,
  })
}

export const getContact = async (id: string | number): Promise<Contact> => {
  return await $fetch<Contact>(`${apiBase()}/api/v1/contacts/${id}`)
}

export const createContact = async (payload: ContactCreate): Promise<Contact> => {
  return await $fetch<Contact>(`${apiBase()}/api/v1/contacts`, {
    method: "POST",
    body: payload,
  })
}

export const patchContact = async (
  id: string | number,
  payload: Partial<Contact>,
): Promise<Contact> => {
  return await $fetch<Contact>(`${apiBase()}/api/v1/contacts/${id}`, {
    method: "PATCH",
    body: payload,
  })
}

export const deleteContact = async (id: string | number): Promise<void> => {
  await $fetch<void>(`${apiBase()}/api/v1/contacts/${id}`, {
    method: "DELETE",
  })
}
