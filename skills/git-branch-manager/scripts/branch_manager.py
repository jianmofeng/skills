#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Git 分支管理技能
功能：从当前 feature/A 分支创建或更新对应的 feature/test/A 分支
"""

import subprocess
import sys
import os
import re


def run_command(cmd, description=""):
    """执行shell命令"""
    print(f"正在{description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout.strip():
            print(result.stdout)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"执行命令失败: {cmd}")
        print(e.stderr)
        raise


def get_current_branch():
    """获取当前分支名称"""
    return run_command("git rev-parse --abbrev-ref HEAD", "获取当前分支")


def branch_exists(branch_name):
    """检查分支是否存在"""
    try:
        run_command(f"git show-ref --verify --quiet refs/heads/{branch_name}")
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print("Git 分支管理技能启动...")

    try:
        current_branch = get_current_branch()
        print(f"当前分支: {current_branch}")

        # 检查是否为 feature/* 形式的分支
        if not current_branch.startswith('feature/') or current_branch.startswith('feature/test/'):
            print('当前不在 feature 分支上，或者已经是 feature/test 分支！')
            sys.exit(1)

        # 构建目标测试分支名称
        feature_parts = current_branch.split('/')[1:]
        feature_part = '/'.join(feature_parts)
        target_branch = f"feature/test/{feature_part}"

        print(f"目标分支: {target_branch}")

        # 拉取最新的远程信息
        run_command("git fetch origin", "拉取远程更新")

        # 检查目标分支是否存在
        if branch_exists(target_branch):
            print(f"分支 {target_branch} 已存在，将合并当前分支到目标分支")

            # 切换到目标分支
            run_command(f"git checkout {target_branch}", f"切换到 {target_branch}")

            # 拉取目标分支最新代码
            run_command(f"git pull origin {target_branch}", f"拉取 {target_branch} 分支最新代码")

            # 合并当前分支到目标分支
            run_command(f"git merge {current_branch}", f"合并 {current_branch} 到 {target_branch}")
        else:
            print(f"分支 {target_branch} 不存在，基于当前分支创建")

            # 基于当前分支创建新的测试分支
            run_command(f"git checkout -b {target_branch}", f"基于 {current_branch} 创建新分支 {target_branch}")

        # 推送目标分支
        run_command(f"git push origin {target_branch}", f"推送 {target_branch} 分支")

        # 尝试使用 GitHub CLI 创建 PR（如果可用）
        try:
            # 检查 GitHub CLI 是否可用
            run_command("gh --version", "检测 GitHub CLI")

            print("检测到 GitHub CLI，正在检查 Pull Request...")

            # 检查是否存在从目标分支到test分支的PR
            try:
                pr_check_result = subprocess.run(
                    f"gh pr list --head {target_branch} --json state --jq '.[0].state'",
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if not pr_check_result.stdout.strip() or pr_check_result.stdout.strip() == "null":
                    print("正在创建 Pull Request...")
                    run_command(
                        f'gh pr create --title "Merge {target_branch} to test" --body "Automated PR from {current_branch} via git branch manager skill\\n\\n- Source branch: {current_branch}\\n- Target branch: test" --base test --head {target_branch}',
                        '创建 Pull Request'
                    )
                else:
                    print("Pull Request 已存在，无需重复创建")
            except Exception as pr_error:
                print(f"PR检查操作失败，但分支已成功更新: {str(pr_error)}")
        except subprocess.CalledProcessError:
            print(f"\n分支操作完成！分支 {target_branch} 已推送至远程。")
            print("如需创建 Pull Request，请手动操作或安装 GitHub CLI。")

        # 切换回原分支
        run_command(f"git checkout {current_branch}", f"切换回 {current_branch}")

        print("\n所有操作完成！分支已成功同步。")
    except Exception as error:
        print(f"\n操作过程中出现错误: {str(error)}")
        sys.exit(1)


if __name__ == "__main__":
    main()