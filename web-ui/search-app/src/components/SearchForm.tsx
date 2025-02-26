import { useState } from "react";
import {
    Box,
    Button,
    Grid,
    GridItem,
    FormControl,
    FormLabel,
    Input,
    Textarea,
    Flex,
    Spinner,
    Text,
} from "@chakra-ui/react";

type SearchFormProps = {
    readonly onSearch: (
        action: string,
        query: string,
        atLeast: number,
        threshold: number,
        atMost: number
    ) => Promise<void>;
}

export default function SearchForm({ onSearch  }: SearchFormProps) {
    const [query, setQuery] = useState("");
    const [atLeast, setAtLeast] = useState(3);
    const [threshold, setThreshold] = useState(0.6);
    const [atMost, setAtMost] = useState(5);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = (action: string) => async (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            setIsLoading(true);

            const timer = setTimeout(() => setIsLoading(false), 10000);
            try {
                // Call the onSearch function
                await onSearch(action, query, atLeast, threshold, atMost);
            } finally {
                clearTimeout(timer);
                setIsLoading(false);
            }

        }
    };

    return (
        <Flex w="100vw" justify="center" pt={4}>
            <Box maxW="600px" w="100%" p={4}>
                <form onSubmit={(e) => e.preventDefault()}>
                    <FormControl mb={4}>
                        <FormLabel>Search Query</FormLabel>
                        <Textarea
                            value={query}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setQuery(e.target.value)}
                            placeholder="Enter search query..."
                            rows={4}
                            isDisabled={isLoading}
                        />
                    </FormControl>

                    <Flex gap={4} mb={4} align="center">
                        <Button
                            type="button"
                            colorScheme="blue"
                            onClick={handleSubmit('search')}
                            //isLoading={isLoading}
                            loadingText="Searching"
                            isDisabled={isLoading || !query.trim()}
                        >
                            Search!
                        </Button>
                        <Button
                            type="button"
                            colorScheme="green"
                            onClick={handleSubmit('rag')}
                            // isLoading={isLoading}
                            loadingText="Processing"
                            isDisabled={isLoading || !query.trim()}
                        >
                            RAG!
                        </Button>

                        {isLoading && (
                            <Flex align="center" ml={2}>
                                <Spinner size="sm" mr={2} />
                                <Text fontSize="sm">Processing request...</Text>
                            </Flex>
                        )}
                    </Flex>

                    <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                        <GridItem>
                            <FormControl>
                                <FormLabel>At Least</FormLabel>
                                <Input
                                    type="number"
                                    value={atLeast}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                        setAtLeast(parseInt(e.target.value) || 3)
                                    }
                                    min={1}
                                    step={1}
                                    isDisabled={isLoading}
                                />
                            </FormControl>
                        </GridItem>
                        <GridItem>
                            <FormControl>
                                <FormLabel>Threshold</FormLabel>
                                <Input
                                    type="number"
                                    value={threshold}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                        setThreshold(parseFloat(e.target.value) || 0.5)
                                    }
                                    min={0}
                                    max={1}
                                    step={0.05}
                                    isDisabled={isLoading}
                                />
                            </FormControl>
                        </GridItem>
                        <GridItem>
                            <FormControl>
                                <FormLabel>At Most</FormLabel>
                                <Input
                                    type="number"
                                    value={atMost}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                        setAtMost(parseInt(e.target.value) || 5)
                                    }
                                    min={1}
                                    step={1}
                                    isDisabled={isLoading}
                                />
                            </FormControl>
                        </GridItem>
                    </Grid>
                </form>
            </Box>
        </Flex>
    );
}