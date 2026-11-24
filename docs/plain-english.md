<!--
Maintainer note. Like README.md, every number and verdict here that comes from the experiment sits between two
invisible markers and is generated from the committed data (`make readme`); tests/test_readme_figures.py checks this
file too. Claude drafted it and he approved it on 2026-11-24, without a disclosure line (his decision).
-->

# Horizon Compact, in plain English

This page is for a reader who wants the whole project in one sitting and will not open the methods page. It says what was asked, what was done, what was found and what it does not show. Every number on it comes from the published results, and the [explorer](https://horizon-compact.vercel.app) shows each one with every run behind it.

## What was asked

Every company is run for someone. For years the Business Roundtable, a group of chief executives of large US companies, said a company is run first for its shareholders. In 2019 it said something wider: that a company is run for all five groups with a stake in it, its customers, employees, suppliers, communities and shareholders. In 2024 the group added that "in the long term, the interests of a company's stakeholders are inseparable." Read plainly, that suggests a company looking far enough ahead would make much the same choices whether it served its shareholders or everyone.

That claim is about the world, and this project cannot test the world. It can test something smaller and still useful, because an AI model can be told who to serve. So the question here is: **if an AI model is told to serve shareholders, or to serve everyone with a stake, does it decide differently? And if it is told to look twenty years ahead, does the difference go away?**

## What was done

**One company, four decisions, five goals.** The project wrote a detailed, made-up manufacturing company and four decisions it faces:

- **Jobs and AI tools.** AI tools can now do the work of 125 office and finance staff. What happens to each person: let go with severance, or retrained for a job in one of the company's plants?
- **Falling orders.** Profit is about to drop. Who absorbs it: the workers, through job cuts or lower pay, or someone else, such as shareholders, customers, suppliers or the company's future products?
- **A plant that loses money.** Close it, retool it or sell it, and decide where its people go.
- **A ten-year program.** The engineers have designed a long, uncertain program to build machines for new customers. Fund it or not?

Then an AI model made each decision many times. From one run to the next, only one thing was changed on purpose: the goal it was given. There were five: serve shareholders, over the next year or over the next twenty years; serve everyone with a stake, over the next year or over twenty years; or no goal at all, as a baseline. Each goal was written three different ways, so that no result rests on one choice of words, and the order of the options was shuffled for every run, so that coming first could help no goal.

**Two models.** The main model was Claude Haiku 5.5, from Anthropic. A second model, OpenAI's gpt-oss-120b, made the same decisions as a check, because one model's habits are not every model's. In all, Haiku 5.5 was asked for <!-- n:grid_runs_haiku -->990<!-- /n --> decisions and gpt-oss-120b for <!-- n:grid_runs_gpt_oss -->1,200<!-- /n -->, on October 14, 2026.

**The plan was published first.** Before a single official decision was made, the project wrote down exactly what it would measure, how, and what each possible result would mean, and published that plan on October 13, 2026. That matters because it is easy, after seeing results, to choose the measures that tell the story you wanted. Here the measures were fixed in advance, and the software refused to run the official experiment if the plan had been changed.

**Everything is published.** Every answer the models gave on the made-up company is in the repository, word for word, with a way to check that none has been altered.

**Then real decisions.** Last, the project tried the same test on a few real business decisions, with the companies' names removed, to see which goal's decisions came closest to what each real company actually did.

## What was found

### Looking twenty years ahead did not make the goals agree

This is the project's main result. On the jobs decision, the main model kept about <!-- n:haiku_cd_s1_points_down -->19<!-- /n --> percentage points fewer of the affected staff when told to serve shareholders over twenty years than when told to serve everyone over twenty years. That is from <!-- n:haiku_cd_s1_runs_c -->60<!-- /n --> decisions under one goal and <!-- n:haiku_cd_s1_runs_d -->60<!-- /n --> under the other, and the true difference most likely lies in the range <!-- n:haiku_cd_s1_interval -->−29.3 to −9.0<!-- /n --> points. Who the model was told to serve still mattered, even with a long horizon.

The same held on two more of the main model's decisions. Told to serve shareholders over twenty years, it chose to close the money-losing plant far more often, about <!-- n:haiku_cd_s3_points_down -->86<!-- /n --> percentage points more, and to fund the ten-year program less often, about <!-- n:haiku_cd_s4_points_down -->41<!-- /n --> points less. The second model showed the same direction on the jobs decision (about <!-- n:gpt_oss_cd_s1_points_down -->45<!-- /n --> points fewer kept) and on the plant (about <!-- n:gpt_oss_cd_s3_points_down -->38<!-- /n --> points more closures). On the remaining decisions, the runs could not tell either way.

### The pattern the Roundtable's words predict did not show up

If a long horizon brought the two goals together, the model would decide differently at one year but the same at twenty years. That never happened, on any decision, for either model. One caution: showing that two goals decide *the same* takes more evidence than showing that they differ, so the project could rarely have confirmed "the same" even if it were true.

### One result went against the project's own expectation

Before any run, the project expected that looking further ahead, or counting more people, would make the model cut less. For the main model, once it was told to serve everyone, looking twenty years ahead instead of one gave about the same result on the jobs decision and on the plant. That is about the one measure each decision was judged by, not every choice the model made. Those <!-- n:against_thesis_count -->2<!-- /n --> results are shown as plainly as the main one, on the site and in the README.

### Over one year, who counts mattered on every decision

For the main model, serving shareholders and serving everyone over the next year gave clearly different decisions on all four.

### The real cases matched no goal

The project's search, using the rule it had fixed in advance, found no real decision that qualified. So it chose <!-- n:cases_exploratory_closures -->5<!-- /n --> real closure decisions afterwards, and labels them as chosen after the fact everywhere they appear. Every one of the <!-- n:cases_readings -->20<!-- /n --> comparisons came out "no good match": none of the goals' decisions looked enough like what the real company did to say it matched. Of the five, <!-- n:cases_leakage_disclosed -->3<!-- /n --> were made public before the main model's training data was gathered, so it may have read about them; each was used only after a test found the models did not remember it.

## What it does not show

- **It is not about people.** It measures how two AI models decide when given a goal in words. It does not measure how real executives decide, and it predicts nothing about any company.
- **It is about these two models.** A small current model and an open-weights model. Larger models, the kind a company might actually put in front of a big decision, could act differently.
- **"No difference found" is not "the same."** Where the runs could not tell two goals apart, that is all it means.
- **It does not judge any company.** The real cases compare a company's decision to the models' decisions. They do not say what the company was trying to do, or whether it was right.
- **The test was written with an AI from the same company as the main model.** Claude, made by Anthropic, drafted the company, the decisions and the goals' wording, and the main model is also made by Anthropic. Readers from other AI companies checked the text before any run, and the second model, from another company, ran the same text. That reduces the worry; it does not remove it.
- **The real cases are a start, not a test.** They were chosen after the planned search found none, there are only five, and none can be re-run by an outsider, because the files describing them are withheld to keep the companies unnamed.

## Where to go next

- [The explorer](https://horizon-compact.vercel.app): every result as a chart, with every run, and the models' own short memos explaining their decisions.
- [How the study was done](https://horizon-compact.vercel.app/methods/): the full goals, the statistics and every known limit.
- [The README](../README.md): the same results for a technical reader, with every verdict and how the project was built.
