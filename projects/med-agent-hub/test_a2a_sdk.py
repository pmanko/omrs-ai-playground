#!/usr/bin/env python3
"""
Test script for A2A SDK agents
Demonstrates using the official A2A SDK to communicate with agents
"""

import asyncio
import logging
import json
import httpx
from uuid import uuid4
from a2a.client import ClientFactory, ClientConfig
from a2a.types import AgentCard, Message, Role, Part, TextPart, TransportProtocol


async def fetch_agent_card(base_url: str, httpx_client: httpx.AsyncClient) -> AgentCard:
    """Fetch AgentCard using the standard .well-known path served by our agents."""
    # Prefer agent.json; fallback to agent-card.json if needed
    for path in ("/.well-known/agent.json", "/.well-known/agent-card.json"):
        try:
            resp = await httpx_client.get(f"{base_url}{path}")
            if resp.status_code == 200:
                return AgentCard(**resp.json())
        except Exception:
            continue
    raise RuntimeError(f"Could not fetch AgentCard from {base_url}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_discovery():
    """Test agent discovery via A2A protocol"""
    logger.info("=" * 60)
    logger.info("Testing Agent Discovery")
    logger.info("=" * 60)
    
    agents = {
        "Router": "http://localhost:9100",
        "MedGemma": "http://localhost:9101",
        "Clinical": "http://localhost:9102"
    }
    
    for name, url in agents.items():
        try:
            async with httpx.AsyncClient() as httpx_client:
                card = await fetch_agent_card(url, httpx_client)
            
            logger.info(f"\n{name} Agent:")
            logger.info(f"  Name: {card.name}")
            logger.info(f"  Description: {card.description}")
            logger.info(f"  Version: {getattr(card, 'version', 'N/A')}")
            logger.info(f"  Skills:")
            
            for skill in card.skills:
                logger.info(f"    - {skill.name}: {skill.description}")
                if hasattr(skill, 'input_schema'):
                    props = skill.input_schema.get('properties', {})
                    logger.info(f"      Inputs: {', '.join(props.keys())}")
                    
            # no client needed for discovery via resolver
            
        except Exception as e:
            logger.error(f"Failed to discover {name} agent: {e}")

async def test_medgemma_agent():
    """Test MedGemma medical Q&A"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing MedGemma Agent")
    logger.info("=" * 60)
    
    httpx_client = httpx.AsyncClient(timeout=180)
    card = await fetch_agent_card("http://localhost:9101", httpx_client)
    client = ClientFactory(ClientConfig(
        httpx_client=httpx_client,
        supported_transports=[TransportProtocol.jsonrpc],
        use_client_preference=False,
    )).create(card)
    
    queries = [
        "What are the common symptoms of hypertension?",
        "How is diabetes type 2 typically managed?",
        "What are the side effects of metformin?"
    ]
    
    for query in queries:
        try:
            logger.info(f"\nQuery: {query}")
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=query))],
                messageId=str(uuid4()),
            )
            captured = []
            async for event in client.send_message(message):
                evt = event[0] if isinstance(event, tuple) else event
                captured.append(str(evt))
            if captured:
                logger.info(f"Streamed events: {captured[-1][:300]}...")
        except Exception as e:
            logger.error(f"Failed to query MedGemma: {e}")
    
    await client.close()
    await httpx_client.aclose()

async def test_clinical_agent():
    """Test Clinical Research agent"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Clinical Research Agent")
    logger.info("=" * 60)
    
    httpx_client = httpx.AsyncClient(timeout=180)
    card = await fetch_agent_card("http://localhost:9102", httpx_client)
    try:
        client = ClientFactory(ClientConfig(
            httpx_client=httpx_client,
            supported_transports=[TransportProtocol.jsonrpc],
            use_client_preference=False,
        )).create(card)
    except Exception as e:
        logger.error(f"Skipping Clinical direct test (client init failed): {e}")
        await httpx_client.aclose()
        return
    
    queries = [
        {"query": "Explain what a randomized controlled trial is.", "scope": "hie"},
    ]
    
    for q in queries:
        try:
            logger.info(f"\nQuery: {q['query']}")
            logger.info(f"Scope: {q.get('scope', 'hie')}")
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=q['query']))],
                messageId=str(uuid4()),
            )
            captured = []
            async for event in client.send_message(message):
                evt = event[0] if isinstance(event, tuple) else event
                captured.append(str(evt))
            if captured:
                logger.info(f"Streamed events: {captured[-1][:300]}...")
            
        except Exception as e:
            logger.error(f"Failed to query Clinical agent: {e}")
    
    await client.close()
    await httpx_client.aclose()

async def test_router_agent():
    """Test Router orchestration"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Router Agent (Orchestration)")
    logger.info("=" * 60)
    
    httpx_client = httpx.AsyncClient(timeout=180)
    card = await fetch_agent_card("http://localhost:9100", httpx_client)
    client = ClientFactory(ClientConfig(
        httpx_client=httpx_client,
        supported_transports=[TransportProtocol.jsonrpc],
        use_client_preference=False,
    )).create(card)
    
    test_cases = [
        {"query": "What are common symptoms of hypertension?", "expected_agent": "medgemma"},
    ]
    
    for test in test_cases:
        try:
            query = test["query"]
            expected = test.get("expected_agent", "unknown")
            
            logger.info(f"\nQuery: {query}")
            logger.info(f"Expected routing: {expected}")
            
            # Build args
            args = {"query": query}
            if "scope" in test:
                args["scope"] = test["scope"]
            if "facility_id" in test:
                args["facility_id"] = test["facility_id"]
            
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=query))],
                messageId=str(uuid4()),
            )
            captured = []
            async for event in client.send_message(message):
                evt = event[0] if isinstance(event, tuple) else event
                captured.append(str(evt))
            if captured:
                logger.info(f"Router streamed events: {captured[-1][:300]}...")
                
        except Exception as e:
            logger.error(f"Failed to query Router: {e}")
    
    await client.close()
    await httpx_client.aclose()

async def test_end_to_end():
    """Test complete flow through the system"""
    logger.info("\n" + "=" * 60)
    logger.info("End-to-End Test via A2A Protocol")
    logger.info("=" * 60)
    
    # Simulate a conversation
    conversation = [
        "What is hypertension?",
        "What medications are typically prescribed for high blood pressure?",
    ]
    
    # Build Router client via resolver + factory
    httpx_client = httpx.AsyncClient(timeout=180)
    card = await fetch_agent_card("http://localhost:9100", httpx_client)
    router_client = ClientFactory(ClientConfig(
        httpx_client=httpx_client,
        supported_transports=[TransportProtocol.jsonrpc],
        use_client_preference=False,
    )).create(card)
    conversation_id = "test-conversation-001"
    
    for i, query in enumerate(conversation, 1):
        try:
            logger.info(f"\n[Turn {i}] User: {query}")
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=query))],
                messageId=str(uuid4()),
            )
            captured = []
            async for event in router_client.send_message(message):
                evt = event[0] if isinstance(event, tuple) else event
                captured.append(str(evt))
            if captured:
                logger.info(f"[Turn {i}] Last event: {captured[-1][:300]}...")
            
        except Exception as e:
            logger.error(f"Failed at turn {i}: {e}")
    
    await router_client.close()
    await httpx_client.aclose()

async def test_clinical_patient_overview():
    """Ask clinical agent for overview of data for a given patient UUID."""
    logger.info("\n" + "=" * 60)
    logger.info("Clinical Patient Overview Test")
    logger.info("=" * 60)

    httpx_client = httpx.AsyncClient(timeout=180)
    card = await fetch_agent_card("http://localhost:9102", httpx_client)
    try:
        client = ClientFactory(ClientConfig(
            httpx_client=httpx_client,
            supported_transports=[TransportProtocol.jsonrpc],
            use_client_preference=False,
        )).create(card)
    except Exception as e:
        logger.error(f"Skipping clinical patient overview (client init failed): {e}")
        await httpx_client.aclose()
        return

    question = "Provide a high-level overview of available clinical data for patient 31f2e621-37c9-4e27-a87d-6689d678b7fd."
    try:
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            messageId=str(uuid4()),
        )
        captured = []
        async for event in client.send_message(message):
            evt = event[0] if isinstance(event, tuple) else event
            captured.append(str(evt))
        if captured:
            logger.info(f"Clinical overview streamed: {captured[-1][:300]}...")
    except Exception as e:
        logger.error(f"Failed clinical patient overview: {e}")
    finally:
        await client.close()
        await httpx_client.aclose()


async def test_simple_router_query():
    """Very simple sanity test: route a basic medical question via Router."""
    logger.info("\n" + "=" * 60)
    logger.info("Simple Router Query Test")
    logger.info("=" * 60)

    httpx_client = httpx.AsyncClient()
    resolver = A2ACardResolver(httpx_client, "http://localhost:9100")
    card = await resolver.get_agent_card()
    client = ClientFactory(ClientConfig(httpx_client=httpx_client)).create(card)

    try:
        result = await client.invoke_skill(
            "route_query",
            query="What are common symptoms of hypertension?",
        )
        logger.info(f"Simple routed result: {str(result)[:300]}")
    finally:
        await client.close()
        await httpx_client.aclose()

async def main():
    """Run all tests"""
    
    # Wait for agents to be ready
    logger.info("Waiting for agents to start...")
    await asyncio.sleep(5)
    
    # Run tests in sequence; never abort whole run on a single failure
    for test in [
        ("discovery", test_agent_discovery),
        ("medgemma", test_medgemma_agent),
        ("clinical", test_clinical_agent),
        ("clinical_patient_overview", test_clinical_patient_overview),
        ("router", test_router_agent),
        ("end_to_end", test_end_to_end),
    ]:
        name, fn = test
        try:
            await fn()
        except Exception as e:
            logger.error(f"Test '{name}' failed: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("All tests completed!")
    logger.info("=" * 60)

if __name__ == "__main__":
    import sys
    
    # Check for --env-file parameter
    env_file = ".env"
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--env-file" and i + 1 < len(sys.argv[1:]):
            env_file = sys.argv[i + 2]
            break
    
    # Load environment from specified file
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    asyncio.run(main())
