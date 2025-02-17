export async function fetchSearchResults(query: string) {
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
            k: 5,
            threshold: 0.3,
            max: 10,
        }),
    });

    if (!response.ok) {
        throw new Error(`Error fetch search results: ${response.statusText}`);
    }

    return response.json();
}
