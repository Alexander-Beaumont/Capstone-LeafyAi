import { API_ROUTES } from "./constants";
import type { APIResult, BABatch, BatchDefinition, GaDefinition, GAGrowingArea, MoveBatch } from "./types";

async function apiRequest<T>(url: string, accessToken?: string, options: RequestInit = {}): Promise<APIResult<T>> {
    try {
        const res = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
                ...options.headers,
            },
        });

        if (!res.ok) {
            let msg = `Request failed (${res.status})`;
            const errBody = await res.json();
            msg = errBody.detail ?? errBody.message ?? msg;
            return { success: false, msg };
        }

        const data = await res.json() as T;
        return { success: true, msg: "", data };
    } catch (error) {
        return { success: false, msg: (error as Error).message };
    }
}

export async function getGrowingAreas(accessToken?: string): Promise<APIResult<GAGrowingArea[]>>{
    return await apiRequest<GAGrowingArea[]>(API_ROUTES.getGrowingAreas, accessToken, {
        method: "GET"
    })
}

export async function getBatches(accessToken: string | undefined): Promise<APIResult<BABatch[]>>{
    return await apiRequest<BABatch[]>(API_ROUTES.getBatches, accessToken, {
        method: "GET"
    })
}

export async function moveBatch(accessToken: string | undefined, moveDetails: MoveBatch): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.moveBatch, accessToken, {
        method: "PATCH",
        body: JSON.stringify(moveDetails),
        headers: {"Content-Type": "application/json",}
    })
}

export async function createGrowingArea(accessToken: string | undefined, gaDetails: GaDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.createGrowingArea, accessToken, {
        method: "POST",
        body: JSON.stringify(gaDetails),
        headers: {"Content-Type": "application/json",}
    })
}

export async function updateGrowingArea(accessToken: string | undefined, gaDetails: GaDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.updateGrowingAreas, accessToken, {
        method: "PATCH",
        body: JSON.stringify(gaDetails),
        headers: {"Content-Type": "application/json",}
    })
}

export async function updateBatch(accessToken: string | undefined, details: {batchID: string, action: "harvest" | "terminate"}): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.updateBatch, accessToken, {
        method: "PATCH",
        body: JSON.stringify(details),
        headers: {"Content-Type": "application/json",}
    })
}

export async function createBatch(accessToken: string | undefined, details: BatchDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.createBatch, accessToken, {
        method: "PATCH",
        body: JSON.stringify(details),
        headers: {"Content-Type": "application/json",}
    })
}