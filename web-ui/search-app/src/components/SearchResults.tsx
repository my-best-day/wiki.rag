import { useState } from 'react';
import { SearchResult } from '../types/SearchResult';

import {
    Box,
    Button,
    Text,
    HStack,
    Accordion,
    AccordionItem,
    AccordionButton,
    AccordionPanel,
    AccordionIcon,
    Stat,
    StatLabel,
    StatNumber,
} from '@chakra-ui/react';

import RelativeTime from '../components/RelativeTime';

type SearchMetadata = {
    completed: string;
    received: string;
    prompt: string;
    answer: string;
};

type SearchResultsProps = {
    readonly results: SearchResult[];
    readonly metadata?: SearchMetadata;
};

export default function SearchResults({ results, metadata }: SearchResultsProps) {
    const [expandedIndices, setExpandedIndices] = useState<number[]>([]);

    // Skip rendering if no results and no metadata
    if (!results.length && !metadata) {
        return null;
    }

    const calculateMetrics = () => {
        if (!metadata) return null;

        const completed = new Date(metadata.completed);
        const completedFormatted = completed.toLocaleTimeString("en-US", { hour12: false });
        const received = new Date(metadata.received);
        const elapsedTime = ((completed.getTime() - received.getTime()) / 1000).toFixed(3);
        const promptTokens = Math.round(metadata.prompt.length / 4.5);
        const promptCost = ((promptTokens * 15) / 1e6).toFixed(4);
        const answerTokens = Math.round(metadata.answer.length / 4.5);
        const answerCost = ((answerTokens * 60) / 1e6).toFixed(4);

        return {
            completed,
            completedFormatted,
            elapsedTime,
            promptTokens,
            promptCost,
            answerTokens,
            answerCost,
        };
    };

    const metrics = calculateMetrics();

    const handleExpandAll = () => {
        setExpandedIndices([...Array(results.length).keys()]);
    };

    const handleCollapseAll = () => {
        setExpandedIndices([]);
    };

    return (
        <Box maxW="800px" mx="auto" p={4}>
            {/* Expand/Collapse Controls */}
            <HStack spacing={4} mb={4} justify="flex-end">
                <Button onClick={handleExpandAll} size="sm">
                    Expand All
                </Button>
                <Button onClick={handleCollapseAll} size="sm">
                    Collapse All
                </Button>
            </HStack>

            {/* Query Info Section */}
            {metadata && metrics && (
                <Box bg="gray.50" p={4} borderRadius="md" mb={4} textAlign="center">
                    <Text fontSize="xs">
                        {`Completed `} <RelativeTime iso={metadata.completed} /> {' '}
                        |{` Elapsed: ${metrics.elapsedTime} sec`} {' '}
                        |{` ${results.length} results`} {' '}
                        |{` in: ${metrics.promptTokens} tokens, ${metrics.promptCost} cents`} {' '}
                        |{` out: ${metrics.answerTokens} tokens, ${metrics.answerCost} cents`}
                    </Text>
                </Box>
            )}

            {/* Results List */}
            <Accordion
                allowMultiple
                index={expandedIndices}
                onChange={(expandedIndex) => setExpandedIndices(expandedIndex as number[])}
            >
                {results.map((result, index) => (
                    <AccordionItem key={result.record[0]}>
                        <AccordionButton py={1}>
                            <Box flex="1">
                                <HStack spacing={4}>

                                    <Text flex="1" textAlign="left" ml={4}>
                                        {index}: {result.caption}
                                    </Text>

                                    <Box width="7.5rem">
                                        <HStack spacing={0} color="gray.500">
                                            <Stat fontSize="xs">
                                                <StatLabel>Similarity: </StatLabel>
                                            </Stat>
                                            <Stat>
                                                <StatNumber fontSize="xs">{result.similarity.toFixed(2)}</StatNumber>
                                            </Stat>
                                        </HStack>
                                    </Box>

                                </HStack>
                            </Box>
                            <AccordionIcon />
                        </AccordionButton>
                        <AccordionPanel pb={4}>
                            <Text maxH="300px" overflowY="auto">
                                {result.text}
                            </Text>
                        </AccordionPanel>
                    </AccordionItem>
                ))}
            </Accordion>
        </Box>
    );
}