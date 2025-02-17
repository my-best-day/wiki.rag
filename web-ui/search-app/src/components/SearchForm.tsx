import { useState } from "react";

type SearchFormProps = {
    onSearch: (query: string) => void;
}

export default function SearchForm({ onSearch }: SearchFormProps) {
    const [query, setQuery] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <label htmlFor="query">Search Query:</label>
            <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query..."
                rows={3}
            />
            <button type="submit">Search</button>
        </form>
    );
}
