<template>
    <div class="orderlist-box">

        <el-tabs v-model="activeTab" type="border-card">
            <el-tab-pane label="候选人列表" name="allOrderList">

                <div class="table-wrapper">

                    <div class="search-area">
                        <el-input placeholder="姓名" v-model="searchBO.realName" prefix-icon="el-icon-user" clearable style="width: 200px; margin-right: 10px; margin-bottom: 8px;"></el-input>
                        <el-input placeholder="手机号" v-model="searchBO.mobile" prefix-icon="el-icon-mobile-phone" clearable style="width: 200px; margin-right: 10px; margin-bottom: 8px;"></el-input>
                        <el-input placeholder="毕业学校" v-model="searchBO.school" prefix-icon="el-icon-school" clearable style="width: 200px; margin-right: 10px; margin-bottom: 8px;"></el-input>
                        <el-input placeholder="专业" v-model="searchBO.major" prefix-icon="el-icon-collection" clearable style="width: 200px; margin-right: 10px; margin-bottom: 8px;"></el-input>
                        <el-button type="primary" size="middle" @click="searchCandidate()">搜索</el-button>
                    </div>

                    <el-table :data="candidateList" border stripe class="table-list">
                        <el-table-column type="index" header-align="center" align="center" width="50"></el-table-column>
                        <el-table-column label="应聘者姓名" header-align="center" align="center" width="120">
                            <template slot-scope="scope">
                                {{scope.row.realName}}
                            </template>
                        </el-table-column>
                        <el-table-column label="身份证号码" header-align="center" align="center" width="180">
                            <template slot-scope="scope">
                                {{scope.row.identityNum}}
                            </template>
                        </el-table-column>
                        <el-table-column label="性别" header-align="center" align="center" width="80">
                            <template slot-scope="scope">
                                <span>
                                    <el-tag type="success" v-if="scope.row.sex == 1">男</el-tag>
                                    <el-tag type="danger" v-if="scope.row.sex == 0">女</el-tag>
                                    <el-tag type="info" v-if="scope.row.sex == 2">保密</el-tag>
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column label="手机号" header-align="center" align="center" width="120">
                            <template slot-scope="scope">
                                {{scope.row.mobile}}
                            </template>
                        </el-table-column>
                        <el-table-column label="邮箱" header-align="center" align="center" width="180">
                            <template slot-scope="scope">
                                {{scope.row.email}}
                            </template>
                        </el-table-column>
                        <el-table-column label="毕业学校" header-align="center" align="center" width="180">
                            <template slot-scope="scope">
                                {{scope.row.school || '-'}}
                            </template>
                        </el-table-column>
                        <el-table-column label="专业" header-align="center" align="center" width="120">
                            <template slot-scope="scope">
                                {{scope.row.major || '-'}}
                            </template>
                        </el-table-column>
                        <el-table-column label="出生日期" header-align="center" align="center" width="120">
                            <template slot-scope="scope">
                                {{ scope.row.birthday || '-' }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="jobName" label="面试岗位" width="150" header-align="center" align="center">
                            <template slot-scope="scope">
                                {{ scope.row.jobName || '-' }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="createTime" label="创建时间" min-width="150" header-align="center" align="center"></el-table-column>

                         <el-table-column label="照片" header-align="center" align="center" width="100">
                            <template slot-scope="scope">
                                <img 
                                    :src="`/img/profile/${scope.row.mobile}.png`"
                                    alt="照片"
                                    style="width: 50px; height: 50px; object-fit: cover;"
                                    @error="e => e.target.outerHTML = '<span style=\'width: 50px; height: 50px; display: inline-block; line-height: 50px; text-align: center;\'>-</span>'"
                                >
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="160" header-align="center" align="center">
                            <template slot-scope="scope">
                                <el-button type="primary" size="mini" plain @click="gotoModifyCandidate(scope.row.candidateId)">编辑</el-button>
                                <el-button type="primary" size="mini" plain @click="deleteCandidate(scope.row.candidateId)">删除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>

                </div>

                <el-pagination
                    background
                    @current-change="doPageList"
                    layout="total, prev, pager, next"
                    :page-size="candidateListPageInfo.pageSize"
                    :total="candidateListPageInfo.records">
                    </el-pagination>

            </el-tab-pane>
        </el-tabs>

    </div>
</template>

<script>
module.exports = {
    data() {
        return {
            activeTab: "allOrderList",

            dialogUserInfoVisible: false,

            searchBO: {
                page: 0,
                pageSize: 0,
                realName: "",
                mobile: "",
                school: "",  // 新增学校搜索字段
                major: ""    // 新增专业搜索字段
            },

            candidateList: [],
            candidateListPageInfo: {
                page: 1,
                pageSize: 10,
                records: 0,     // 总记录数
                total: 0,       // 总页数
            },
        }
    },
    mounted() {
        this.initCandidateList(1, this.candidateListPageInfo.pageSize);
    },
    methods: {

        initCandidateList(page, pageSize) {

            var searchBO = this.searchBO;
            searchBO.page = page;
            searchBO.pageSize = pageSize;

            console.log(searchBO);

            candidateApi.list(searchBO).then(response => {
                console.log(response);
                var candidateList = response.data.rows;
                this.candidateList = candidateList;

                this.candidateListPageInfo.records = response.data.records;
                this.candidateListPageInfo.total = response.data.total;
                this.candidateListPageInfo.page = page;
                this.candidateListPageInfo.pageSize = pageSize;
            });
        },

        doPageList(page) {
            this.initCandidateList(page, this.candidateListPageInfo.pageSize);
        },

        searchCandidate() {
            var bo = this.searchBO;
            console.log(bo);

            this.initCandidateList(1, this.candidateListPageInfo.pageSize);
        },

        gotoModifyCandidate(candidateId) {
            var targetPath = "/candidateMng/candidateCreate?candidateId=" + candidateId;
            this.$parent.$router.push({
                path: targetPath
            });
        },

        deleteCandidate(candidateId) {

            this.$confirm('确认删除该候选人吗？', '提示', {
                confirmButtonText: '确认删除',
                cancelButtonText: '容我三思',
                type: 'warning'
            }).then(() => {

                candidateApi.delete(candidateId).then(response => {
                    console.log(response);

                    this.$message({
                        showClose: true,
                        message: '候选人删除成功!',
                        type: 'success',
                        duration: 2000
                    });

                    this.initCandidateList(1, this.candidateListPageInfo.pageSize);
                });

            }).catch(() => {
            });

        },

    },
}
</script>

<style>
.orderlist-box {
    /* padding: 10px; */

    display: flex;
    flex-direction: column;
    justify-content: flex-start;

    /* border: solid 10px #e3e9ef; */

    font-size: 16px;
}

.orderlist-box .table-wrapper {
    padding: 10px 10px 20px 10px;
}

.orderlist-box .table-list {
    width: 100%;
    font-size: 15px;
}

.orderlist-box .search-area {
    margin-bottom: 20px;
}

</style>