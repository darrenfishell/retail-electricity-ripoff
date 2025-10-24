---
style: "./styles/style.css"
---

```js
const json_content = await FileAttachment(`data/cost_comparison.json`).json();
const cost_db = await DuckDBClient.of({cost_db: json_content});
const year_summary = await cost_db.sql`
    SELECT 
        year::INTEGER as year, 
        SUM(res_cost_variance) AS variance
    FROM cost_db
    GROUP BY year
`;
const premium_total_result = Array.from(await cost_db.sql`
    SELECT 
        SUM(res_cost_variance) AS total_variance,
        MIN(year) AS min_year,
        MAX(year) AS max_year
    FROM cost_db
`);
const total_variance = premium_total_result[0]?.total_variance;
const formatted_total = "$" + (total_variance / 1_000_000).toFixed(0) + "M";
const year_range = premium_total_result[0]?.min_year + " - " + premium_total_result[0]?.max_year
const dark = Generators.dark();
```

```js
const text_fill = dark ? 'white' : 'black';
```

<div class="hero">

# Maine's $200M (and counting) retail electricity ripoff

## Each year since 2013, Maine customers have paid more than they needed to for electricity. If customers had taken the standard offer instead of buying service from retail suppliers, who sometimes sell door-to-door, they would have saved ${formatted_total} from ${year_range}.

</div>

```js
function createAnnualPremiumChart({
                                      data,
                                      totalAmount,
                                      yearRange,
                                      width = 500,
                                      height = 400,
                                      barColor = "steelBlue",
                                      title = null
                                  }) {
    return Plot.plot({
        title: title || `Retail supplier charges above the standard offer`,
        subtitle: `Comparing aggregate sales/kwh to a weighted standard offer from ${year_range}`,
        width: Math.max(500, width),
        marginTop: 100,
        className: 'custom-plot',
        height: height,
        x: {
            label: "Year",
            scale: {
                type: 'band',
                interval: 2
            },
            tickFormat: (d) => `${d}`
        },
        y: {
            grid: true,
            label: "Cost over standard offer"
        },
        marks: [
            Plot.rectY(data, {
                x: "year",
                y: "variance",
                fill: barColor,
                target: "_top"
            }),
            Plot.text(data, {
                x: "year",
                y: "variance",
                text: d => "$" + (d.variance / 1_000_000).toFixed(1) + "M",
                dy: -6, // move the label a bit above the top of the bar
            }),
            Plot.axisY({
                marginLeft: 50,
                tickFormat: d => "$" + (d / 1_000_000).toFixed(0) + "M"
            }),
            Plot.axisX({
                tickFormat: d => d.toString(),
                label: null
            }),
            Plot.tip(
                [`Electricity Maine makes up 81 percent of the market in this year, by kWh sales.`],
                {
                    x: 2015,
                    y: 37_000_000,
                    dy: -10,
                    anchor: "bottom",
                    fill: 'white'
                },
            )

        ]
    });
}

// Use the function to create and display the chart
const barChart = createAnnualPremiumChart({
    data: year_summary,
    totalAmount: formatted_total,
    yearRange: year_range,
    width: width,
    height: 400
});

display(barChart)
```

```js
// Query data by utility company for the bubble chart
const utility_summary = await cost_db.sql`
    SELECT 
        utility_name AS name,
        SUM(res_cost_variance) AS cost_variance,
        SUM(sales_kwh) as sales_kwh
    FROM cost_db
    GROUP BY utility_name
    ORDER BY cost_variance DESC
`;

const utilityChart = Plot.plot({
    title: 'Charges to customers above the standard offer',
    subtitle: `Comparing aggregate sales/kwh to a weighted standard offer from ${year_range}`,
    className: 'custom-plot',
    marks: [
        Plot.barX(utility_summary, {
            x: "cost_variance",
            y: "name",
            fill: "steelblue",  // Add color to the bars
            tip: true,
            sort: {y: "x", reverse: true}
        }),
        Plot.axisY({
            marginLeft: width / 3.25,
            label: null
        }),
        Plot.axisX({
            tickFormat: d => "$" + (d / 1_000_000).toFixed(0) + "M",
            label: null
        }),
        // Optional: Add values at the end of each bar
        Plot.text(utility_summary, {
            x: "cost_variance",
            y: "name",
            text: d => "$" + (d.cost_variance / 1_000_000).toFixed(2) + "M",
            dx: 5,
            textAnchor: "start",
            marginRight: 100,
            sort: {y: "x", reverse: true}
        })
    ],
    x: {
        label: "Cost Variance ($)",
        tickFormat: d => "$" + (d / 1_000_000).toFixed(0) + "M",
        scale: {
            type: 'band',
            interval: 40_000_000
        },
    }
});

const utility = view(utilityChart)
```

```js
// Query time series data for the line chart with updated SQL
const price_trends = await cost_db.sql`
    SELECT * FROM
        (SELECT
            year::INTEGER AS year,
            AVG(kwh_rate) AS avg_price,
            'Retail supplier' AS category
        FROM cost_db
        WHERE utility_name = ${utility?.name}
            OR ${utility?.name ?? 'all'} = 'all'
        GROUP BY year
        UNION ALL
        SELECT 
            year::INTEGER AS year,
            AVG(weighted_standard_offer) AS avg_price,
            'Standard offer' AS category
        FROM cost_db
        GROUP BY year
    ) ORDER BY year
`;

// Create an interactive line chart with hover effects
const lineChart = Plot.plot({
    title: `Electricity Price Trends: Standard Offer vs. Retail Rates`,
    subtitle: `Plotted against the annual average for ${utility?.name ?? 'all suppliers'}`,
    className: "custom-plot",
    color: {legend: true},
    x: {label: "Year"},
    y: {
        label: "Price (¢/kWh)",
        zero: true
    },
    marks: [
        // Add a horizontal zero line
        Plot.ruleY([0]),
        Plot.axisX({
            tickFormat: d => d.toString()
        }),
        // Retail price line
        Plot.line(price_trends, {
            x: "year",
            y: "avg_price",
            stroke: 'category',
            tip: true,
            title: d => `Year: ${d.year}\nRetail Price: $${d.avg_price.toFixed(2)}¢/kWh`
        }),
        // Add label for standard offer line using select transform to get the last point
        Plot.text(price_trends, Plot.selectLast({
                x: "year",
                y: "avg_price",
                z: 'category',
                text: (d) => '$' + (d.avg_price).toFixed(2) + '/kwh',
                frameAnchor: "right",
                dx: -5
            }
        ))
    ]
});

const line_trend = view(lineChart)
```

<div class="dashboard">

<div class="grid grid-cols-2" style="gap: 1rem; align-items: start;">
    <div class="chart-container">
      ${utilityChart}
    </div>
    <div class="chart-container">
      ${lineChart}
    </div>
</div>
</div>

_Some suppliers, such as Clearview Electric, offered electricity supplied by renewable sources, at a premium cost. In
most cases, retail suppliers acquire power from sources that match the regional mix of power generation._

## About the data

This project sources data from the U.S. Energy Information Administration and the Maine Public Utilities Commission. For details on the data pipeline and transformations, refer to the project [Github repository](https://github.com/darrenfishell/retail-electricity).

This pipeline is a dramatic improvement over the Tableau Prep and manual data wrangling used for some of the very first analyses. Rebuilding this with more flexible code-first tools has long been on my list. As was rebuilding the core visualizations with Observable Plot instead of Tableau.

## Reporting background

The analysis provides context for a series of reporting I conducted for the Bangor Daily News and the Maine Monitor, both which provided some important additional context for the data. Regulators have called attention to bad practices in the industry for many years, as has the state's public advocate, but the general trend continues of the retail market costing customers more.

The last time I reported on the subject for any outlet was 2020, for The Maine Monitor, when the forgone savings totaled $132 million. As of this writing (2025), it now totals $185.5 million.

> Maine Monitor: [The $132M electricity rip-off](https://themainemonitor.org/private-electricity-suppliers-cost-mainers-132-million-more-than-necessary/)

The total continues to astound me, but the context and methods of some prior reporting are just as important. Below are some key points and a list of stories (BDN paywall applies) that detail some of the important other trends regarding regulator complaints, lawsuits and deceptive marketing tactics. 

### The retail supplier response

Historically, the industry contends the analysis is not an apples-to-apples comparison with the standard offer, because they can offer electricity that, for example, has a greater share of renewable power or other attributes. 

However, each retail supplier is required to provide a disclosure statement of this power mix for the plans they provide and this, most often, matches exactly the mix in the standard offer, for the largest suppliers. Tim Schneider, the state's public advocate in 2016, said "The innovation that we’ve seen has been around customer acquisition, and not in the products that they’re offering."

For years, the biggest retail supplier in state was quiet about this reporting and follow-up analysis by the Maine Public Utilities Commission that used the same methodology to make this comparison.

> BDN: [State confirms home power customers spent $77M they didn't need to](https://www.bangordailynews.com/2018/02/21/mainefocus/state-confirms-home-power-customers-spent-77m-they-didnt-need-to/)

But in 2019, one of Electricity Maine's co-founders said of the PUC report, "I don't think it's a valuable report." He proceeded in [a sworn deposition (pg. 131)](https://github.com/darrenfishell/darrenfishell.github.io/blob/master/public-docs/EMaine%20class%20action/clavet-deposition.pdf) to state that he did not know whether his company charged customers less than the standard offer, on average, in 2014 or 2015.

When the company entered the market in 2011, Clavet promised "We will always beat the standard offer. You’ll never, ever pay more than the standard offer, or we won’t be back." (Ironically, the literal headline of this [story in the Lewiston Sun Journal](https://perma.cc/W2U7-UFH7) was "Maine’s newest electricity suppliers seem too good to be true")

(The deposition was part of a class-action lawsuit that stemmed from my first stories on the topic.)

> BDN: [Ex-customers sue Electricity Maine for $35M, claim company defrauded thousands](https://www.bangordailynews.com/2016/11/18/news/ex-customers-sue-electricity-maine-for-35m-claim-company-defrauded-thousands/)

In 2016, Clavet and his partner Kevin Dean agreed to sell Electricity Maine to the Texas-based Spark Energy with an earnout provision that specifically incentivized them to sign up new customers [at a rate roughly 35 percent higher than the standard offer at the time](https://www.documentcloud.org/documents/2998320-Spark-Energy-purchase-agreement-for-Provider-Power/#document/p69/a313349).

“It was a little bit discouraging because, you know, to get anywhere really with it, you had to sell a lot of electricity at a pretty strong price compared to what the current market was to a fair number of customers using, you know, a method, which for us was mostly direct mail that yielded very few results,” [Clavet said](https://www.documentcloud.org/documents/6576657-Clavet-Trial-Testimony.html#document/p2/a540353).

While Clavet waffled on the price comparison during his 2019 deposition, I'd agree with the characterization that Electricity Maine charged and that Maine customers paid "a pretty strong price." 

The real kicker is, Dean and Clavet themselves paid a pretty strong price. As part of a personal lawsuit between the two former business partners, Dean stated in 2018 that the company had loses of over $14 million in 2015 and its operations throughout Northern New England "were in trouble." As noted in the very first chart above, Electricity Maine made up 81 percent of the market in that year.

> BDN: [Electricity company overcharged customers millions, but was still losing money](https://www.bangordailynews.com/2018/05/22/energy/while-electricity-maine-overcharged-customers-millions-it-was-still-losing-money/)

The initial batch of stories led to some [new state consumer protections regarding rate hikes for retail suppliers](https://www.bangordailynews.com/2017/05/16/news/new-limits-on-electricity-sellers-sent-to-lepage/), but customers continued to lose money to these companies at a steady clip. 

The [state's public advocate in 2023](https://wgme.com/news/local/public-advocate-maine-competitive-power-supply-market-cmp-central) said that the retail market (called "competitive suppliers" in state statute) has failed in its primary goal to lower rates and that it should be shut down.

### Poles, wires and bills vs. supply

One of the most important details about this story and this reporting is also one of the most boring: the utility companies that send out bills to customers don't actually sell you electricity. They do bill you, and they do maintain all of the infrastructure for billing you, but they are just processing the bill for the actual electricity supply, which is broken out on a bill. Bills do also include charges directly from the utility, for transmission and distribution and other costs ([sample CMP bill](https://www.cmpco.com/account/understandyourbill/sample-bill)). This was part of deregulation of Maine's electricity market in the early 2000s. 

But it wasn't until 2012 that any suppliers showed up to offer a real alternative to customers from the standard offer, which is also not supplied by the utilities. The standard offer is just a bulk deal that state regulators solicit bids on from other large regional suppliers on a regular basis (now annual).

At the time that the residential retail market started, the state bought this electricity over a rolling three-year period in the interest of isolating customers from large year-over-year fluctuations in the price. This method was part of the slow price response that created the opportunity for Electricity Maine. As electricity prices on the open market dipped in 2012, the standard offer still priced in contracts going back three years. 

Buying just for one year ahead, Electricity Maine was able to undercut the standard offer substantially and save customers $3 million. That was the only year that the market, as a whole, did this for residential customers.

Confusion around this separation is another key part of this story because the companies involved have consistently used this to their advantage in marketing themselves.

### Going door-to-door

Where Clavet said he and Dean had trouble acquiring customers with direct mail, their successor, Spark Energy, and other retail electric suppliers turned to other marketing tactics to get customers to sign up. 

In many cases, regulators faced complaints that these salespeople were either misrepresenting themselves as power company employees or letting the customers think as much. They could use this relationship two ways: channeling customers ire towards conversion to their power supply and also fueling that ire from confusion over how a power bill is broken out. 

> BDN: [Electricity sellers use Facebook to cash in on complaints about surging CMP bills](https://www.bangordailynews.com/2018/03/09/mainefocus/electricity-sellers-use-facebook-to-cash-in-on-complaints-about-surging-cmp-bills/)

In the story above, I found one case of a TV news interview with a landlord who touted the energy savings with one provider, Ambit. The landlord featured did not disclose that he was a sales consultant with the company, which was the only supplier at the time using a multi-level marketing structure for selling electricity in the state. 

Regulators separately fielded various complaints about electricity sellers posing as CMP auditors in order to have customers hand over a recent bill. Access to a customer bill would provide a salesperson for an electricity supplier all of the information they would need to sign up a new customer for the service. Of course, after the change, the customer would still receive their bills from the utility, but now with a higher price for their supply charge.

> BDN: [Electricity sellers allegedly posed as CMP auditors to poach customers](https://www.bangordailynews.com/2018/06/22/business/electricity-sellers-allegedly-posed-as-cmp-auditors-to-poach-customers/)

Unless they specifically scrutinized the supplier name on the bill, they could easily leave with ire toward the power company, an accessible and durable punching bag.

### Secondary markets

The growth of the retail market spawned still more confusion, as websites and services offering help navigating all of the different suppliers popped up across New England. In some cases, however, the purportedly independent information brokers had relationships themselves with electricity suppliers. 

> BDN: [New electricity shopping sites mislead customers, watchdog warns](https://www.bangordailynews.com/2018/07/24/mainefocus/new-electricity-shopping-sites-mislead-customers-watchdog-warns/)

Elin Katz, Connecticut's Consumer Counsel in 2018, said at the time "They’re just trying to sell you one of four suppliers who pay them."

### What's ahead

In March, the newly appointed public advocate, Heather Sanborn, sought to get detailed geographic data from retail suppliers on the markets that they serve, hoping to understand demographic trends in those areas.

> Press Herald: [Maine’s public advocate seeks access to billing data from electricity suppliers](https://www.pressherald.com/2025/03/19/maines-advocate-seeks-access-to-billing-data-from-electricity-suppliers/)

The primary question is whether the companies are operating in disproportionately low-income areas. The Maine State Chamber of Commerce and representatives for retail suppliers oppose the request.