import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.7.1";

interface BreachData {
  hash: string;
  entity: string;
  breach_date?: string;
  notice_date?: string;
  records: number;
  breach_type?: string;
  entity_type?: string;
  state?: string;
  notice_url?: string;
  _portal: string;
}

interface ResearchResult {
  sources: string[];
  findings: string;
}

interface Summary {
  text: string;
  severity: string;
  impact_assessment: string;
  recommendations: string[];
  sources: string[];
  generated_at: string;
}

serve(async (req) => {
  try {
    const row = await req.json() as BreachData;
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseKey = Deno.env.get("SUPABASE_KEY");
    const firecrawlApiKey = Deno.env.get("FIRECRAWL_API_KEY");

    if (!supabaseUrl || !supabaseKey) {
      return new Response(JSON.stringify({ error: "Missing Supabase environment variables" }), {
        headers: { "Content-Type": "application/json" },
        status: 500
      });
    }

    if (!firecrawlApiKey) {
      console.warn("Missing Firecrawl API key, using simplified research");
    }

    const supa = createClient(supabaseUrl, supabaseKey);

    // Step 1: Research the breach using Firecrawl
    const researchResult = await researchBreach(row, firecrawlApiKey);

    // Step 2: Generate a comprehensive summary using AI
    const summary = await generateSummary(row, researchResult);

    // Step 3: Store the summary in Supabase
    await supa.from('breach_ai').insert({
      hash: row.hash,
      summary: summary
    });

    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    console.error("Error processing breach:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { "Content-Type": "application/json" },
      status: 500
    });
  }
});

async function researchBreach(breach: BreachData, apiKey?: string): Promise<ResearchResult> {
  try {
    if (!apiKey) {
      // Simplified research without Firecrawl API key
      return {
        sources: [],
        findings: `Limited information available for ${breach.entity} breach affecting ${breach.records} individuals.`
      };
    }

    // Use Firecrawl deep research to find information about the breach
    const searchQuery = `${breach.entity} data breach ${breach.breach_date || breach.notice_date || ""} ${breach.state || ""}`;

    const response = await fetch("https://api.firecrawl.dev/deep_research", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        query: searchQuery,
        maxDepth: 3,
        timeLimit: 120,
        maxUrls: 10
      })
    });

    if (!response.ok) {
      throw new Error(`Firecrawl API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    return {
      sources: data.sources || [],
      findings: data.finalAnalysis || `Research on ${breach.entity} breach was inconclusive.`
    };
  } catch (error) {
    console.error("Research error:", error);
    return {
      sources: [],
      findings: `Error researching breach: ${error.message}`
    };
  }
}

async function generateSummary(breach: BreachData, research: ResearchResult): Promise<Summary> {
  try {
    // Determine severity based on records and breach type
    let severity = "low";
    if (breach.records > 100000) {
      severity = "critical";
    } else if (breach.records > 10000) {
      severity = "high";
    } else if (breach.records > 1000) {
      severity = "medium";
    }

    // Generate recommendations based on breach type
    const recommendations = generateRecommendations(breach.breach_type);

    // For a production environment, you would integrate with an AI model API here
    // This is a simplified version that creates a structured summary
    const summary: Summary = {
      text: research.findings || `Breach at ${breach.entity} affecting ${breach.records} individuals.`,
      severity,
      impact_assessment: generateImpactAssessment(breach),
      recommendations,
      sources: research.sources,
      generated_at: new Date().toISOString()
    };

    return summary;
  } catch (error) {
    console.error("Summary generation error:", error);
    return {
      text: `Breach at ${breach.entity} affecting ${breach.records} individuals.`,
      severity: breach.records > 10000 ? "high" : "medium",
      impact_assessment: "Unable to assess impact due to an error.",
      recommendations: ["Monitor your accounts for suspicious activity."],
      sources: [],
      generated_at: new Date().toISOString()
    };
  }
}

function generateImpactAssessment(breach: BreachData): string {
  const recordsDescription =
    breach.records > 1000000 ? "millions of" :
    breach.records > 100000 ? "hundreds of thousands of" :
    breach.records > 10000 ? "tens of thousands of" :
    breach.records > 1000 ? "thousands of" :
    breach.records > 100 ? "hundreds of" : "some";

  let assessment = `This breach at ${breach.entity} has affected ${recordsDescription} individuals`;

  if (breach.breach_type) {
    assessment += ` through a ${breach.breach_type.toLowerCase()} incident`;
  }

  if (breach.state) {
    assessment += ` in ${breach.state}`;
  }

  assessment += `. The breach was ${breach.notice_date ? `reported on ${breach.notice_date}` : "recently reported"}`;

  if (breach.breach_date && breach.breach_date !== breach.notice_date) {
    assessment += ` but occurred on ${breach.breach_date}`;
  }

  assessment += ".";

  return assessment;
}

function generateRecommendations(breachType?: string): string[] {
  const commonRecommendations = [
    "Monitor your accounts for suspicious activity.",
    "Consider placing a fraud alert or credit freeze with the major credit bureaus."
  ];

  if (!breachType) {
    return [...commonRecommendations, "Change passwords for affected accounts."];
  }

  const typeSpecificRecommendations: Record<string, string[]> = {
    "HACK": [
      "Change passwords for all accounts, especially if you reuse passwords.",
      "Enable two-factor authentication where available."
    ],
    "CARD": [
      "Contact your bank to request a new card.",
      "Review recent transactions for unauthorized charges."
    ],
    "INSD": [
      "Be cautious of potential phishing attempts using your personal information.",
      "Consider identity theft protection services."
    ],
    "PHYS": [
      "Monitor mail for suspicious items or missing expected items.",
      "Consider using a P.O. box or secure mail service."
    ],
    "PORT": [
      "Change passwords for all accounts stored on the lost device.",
      "If applicable, use remote wipe features to clear data."
    ],
    "DISC": [
      "Monitor accounts for suspicious activity.",
      "Be cautious of unexpected communications claiming to be from the affected organization."
    ]
  };

  // Normalize breach type for matching
  const normalizedType = breachType.toUpperCase().substring(0, 4);

  return [
    ...commonRecommendations,
    ...(typeSpecificRecommendations[normalizedType] || ["Change passwords for affected accounts."])
  ];
}
