export async function fetchSearchResults(query: string, atLeast: number, threshold: number, atMost: number) {
    const response = await fetch("http://localhost:8023/api/combined", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            id: "1",
            action: "search",
            kind: "segment",
            query: query,
            k: atLeast,
            threshold: threshold,
            max: atMost,
        }),
    });

    if (!response.ok) {
        throw new Error(`Error fetch search results: ${response.statusText}`);
    }

    return response.json();
}
