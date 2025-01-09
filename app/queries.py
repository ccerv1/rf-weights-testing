retrofunding_graph = """ 
with 
    -- Step 1: Relevant Projects with Metrics
    relevant_projects as (
        select distinct
            project_id,
            project_name
        from `oso_production.onchain_metrics_by_project_v1`
        where
            event_source in ('OPTIMISM', 'BASE', 'MODE', 'ZORA')
            and transaction_count_6_months > 1000
            and project_id in (
                select project_id from `oso_production.projects_by_collection_v1`
                where collection_name = 'op-retrofunding-4'
            )
    ),

    -- Step 2: Relevant Repositories
    relevant_repos as (
        select
            r.artifact_id,
            r.project_id,
            rp.project_name,
            r.language
        from `oso_production.repositories_v0` r
        join relevant_projects rp on r.project_id = rp.project_id
        where 
            r.language in ('TypeScript', 'Solidity', 'Rust')
    ),

    -- Step 3: Core Developers
    core_devs as (
        select
            e.from_artifact_id as developer_id,
            u.display_name as developer_name,
            e.to_artifact_id as repo_id
        from `oso_production.int_events__github` e
        join `oso_production.users_v1` u
        on e.from_artifact_id = u.user_id
        where e.to_artifact_id in (select artifact_id from relevant_repos)
            and e.event_type = 'COMMIT_CODE'
            and u.display_name not like '%[bot]%'
        group by 1,2,3
        having
            count(distinct date_trunc(time, month)) >= 3
            and sum(amount) >= 20
    ),

    -- Step 4: Repositories with Releases
    repos_with_releases as (
        select distinct to_artifact_id
        from `oso_production.int_events__github`
        where event_type = 'RELEASE_PUBLISHED'
    ),

    -- Step 5: Developer Interactions with Dev Tools
    dev_interactions as (
        select
            rr.project_id as `Project ID`,
            rr.project_name as `Project Name`,
            target_p.project_id as `Dev Tool ID`,
            target_p.project_name as `Dev Tool Name`,
            cd.developer_id as `Developer ID`,
            count(distinct cd.developer_id) as `Num Project Devs Engaging with Dev Tool`
        from core_devs cd
        join relevant_repos rr on cd.repo_id = rr.artifact_id
        join `oso_production.int_events__github` e on cd.developer_id = e.from_artifact_id
        left join `oso_production.repositories_v0` target_rm on e.to_artifact_id = target_rm.artifact_id
        left join `oso_production.projects_v1` target_p on target_rm.project_id = target_p.project_id
        where e.to_artifact_id not in (select artifact_id from relevant_repos)
            and e.to_artifact_id in (select to_artifact_id from repos_with_releases)
            and e.time >= '2023-01-01'
            and target_p.project_id in (
                select project_id from `oso_production.projects_by_collection_v1`
                where collection_name = 'op-rpgf3'
            )
        group by 1,2,3,4,5
    ),

    -- Step 6: Dependency Relationships
    dependency_relationships as (
        select
            sboms.from_project_id as `Project ID`,
            onchain_builders.project_name as `Project Name`,
            dev_tools.project_id as `Dev Tool ID`,
            dev_tools.project_name as `Dev Tool Name`,
            'Dependency' as `Relationship Type`
        from `oso_production.sboms_v0` as sboms
        join `oso_production.projects_by_collection_v1` as onchain_builders
            on sboms.from_project_id = onchain_builders.project_id
        join `oso_production.package_owners_v0` as pkgs
            on sboms.to_package_artifact_name = pkgs.package_artifact_name
            and sboms.to_package_artifact_source = pkgs.package_artifact_source
        join `oso_production.projects_v1` as dev_tools
            on pkgs.package_owner_project_id = dev_tools.project_id
        where
            onchain_builders.collection_name = 'op-retrofunding-4'
            and dev_tools.project_id in (
                select project_id from `oso_production.projects_by_collection_v1`
                where collection_name = 'op-rpgf3'
            )
        group by 1,2,3,4
    ),

    -- Step 7: Smart Contract Developers for Each Project
    smart_contract_devs as (
        select distinct
            cd.developer_id as `Smart Contract Developer ID`,
            rr.project_id as `Project ID`
        from core_devs cd
        join relevant_repos rr on cd.repo_id = rr.artifact_id
        where rr.language = 'Solidity'
    ),

    -- Step 8: Combined Relationships
    combined_relationships as (
        select
            coalesce(e.`Project ID`, d.`Project ID`) as `Project ID`,
            coalesce(e.`Project Name`, d.`Project Name`) as `Project Name`,
            coalesce(e.`Dev Tool ID`, d.`Dev Tool ID`) as `Dev Tool ID`,
            coalesce(e.`Dev Tool Name`, d.`Dev Tool Name`) as `Dev Tool Name`,
            case
                when e.`Project ID` is not null and d.`Project ID` is not null then 'Both'
                when e.`Project ID` is not null then 'Engagement'
                when d.`Project ID` is not null then 'Dependency'
            end as `Relationship Type`
        from dev_interactions e
        full outer join dependency_relationships d
        on e.`Project ID` = d.`Project ID`
        and e.`Dev Tool ID` = d.`Dev Tool ID`
    )

-- Final Output: Unified Table
select
    cr.`Project ID`,
    cr.`Project Name`,
    cr.`Dev Tool ID`,
    cr.`Dev Tool Name`,
    cr.`Relationship Type`,
    count(distinct di.`Developer ID`) as `Num Project Devs Engaging with Dev Tool`,
    count(distinct case when scd.`Project ID` = cr.`Project ID` then scd.`Smart Contract Developer ID` end) as `Num Smart Contract Devs Engaging with Dev Tool`,    
    sum(om.transaction_count_6_months) as `Project Total Txns`,
    sum(om.gas_fees_sum_6_months) as `Project Total Gas Fees`
from combined_relationships cr
left join `oso_production.onchain_metrics_by_project_v1` om on cr.`Project ID` = om.project_id
left join dev_interactions di on cr.`Project ID` = di.`Project ID` and cr.`Dev Tool ID` = di.`Dev Tool ID`
left join smart_contract_devs scd on cr.`Project ID` = scd.`Project ID`
group by 1,2,3,4,5
order by `Project ID`
"""