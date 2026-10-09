<template>
    <div class="orderCreate-box">

        <el-tabs v-model="activeTab" type="border-card">
            <el-tab-pane :label="activeTitle" name="createCandidate">

                <div class="table-wrapper">
                    
                    <el-form ref="candidateForm" :model="candidateForm" :rules="rules" label-width="120px">
                        <el-row :gutter="30">
                            <el-col :span="12">
                                <h4 class="form-group-title">个人基本信息</h4>
                                <el-form-item label="面试岗位" prop="jobId">
                                    <el-select v-model="candidateForm.jobId" placeholder="请选择面试岗位" style="width: 100%;">
                                        <el-option
                                            v-for="item in jobNameList"
                                            :key="item.jobId"
                                            :label="item.jobName"
                                            :value="item.jobId">
                                        </el-option>
                                    </el-select>
                                </el-form-item>

                                <el-form-item label="姓名" prop="realName">
                                    <el-input v-model="candidateForm.realName" style="width: 100%;" maxlength="12"></el-input>
                                </el-form-item>
                                  <el-form-item label="性别" prop="sex">
                                      <el-select v-model="candidateForm.sex" placeholder="请选择性别" style="width: 100%;">
                                          <el-option label="保密" value="2"></el-option>
                                          <el-option label="女" value="0"></el-option>
                                          <el-option label="男" value="1"></el-option>
                                      </el-select>
                                  </el-form-item>
                                  <el-form-item label="身份证号码" prop="identityNum">
                                      <el-input v-model="candidateForm.identityNum" style="width: 100%;" maxlength="18"></el-input>
                                  </el-form-item>
                                  <el-form-item label="邮箱" prop="email">
                                      <el-input v-model="candidateForm.email" style="width: 100%;"></el-input>
                                  </el-form-item>
                                <el-form-item label="手机号" prop="mobile">
                                    <el-input v-model="candidateForm.mobile" style="width: 100%;" maxlength="11"></el-input>
                                </el-form-item>
                                <el-form-item label="出生日期">
                                    <el-date-picker value-format="yyyy-MM-dd" type="datetime" placeholder="请选择出生日期" v-model="candidateForm.birthday" style="width: 360px;"></el-date-picker>
                                </el-form-item>
                                <h4 class="form-group-title">个人资质</h4>
                                <el-form-item label="证书" prop="certificate">
                                    <el-input v-model="candidateForm.certificate" style="width: 100%;"></el-input>
                                </el-form-item>
                                <el-form-item label="荣誉" prop="awards">
                                    <el-input v-model="candidateForm.awards" style="width: 100%;"></el-input>
                                </el-form-item>
                            </el-col>
                            <el-col :span="12">
                                <h4 class="form-group-title">个人经历</h4>
                                <el-form-item label="学校" prop="school">
                                    <el-input v-model="candidateForm.school" style="width: 100%;"></el-input>
                                </el-form-item>
                                <el-form-item label="专业" prop="major">
                                    <el-input v-model="candidateForm.major" style="width: 100%;"></el-input>
                                </el-form-item>
                                <el-form-item label="项目经历" prop="experiment">
                                    <el-input type="textarea" :rows="3" v-model="candidateForm.experiment" style="width: 100%;"></el-input>
                                </el-form-item>

                                <el-form-item label="自我介绍" prop="introduce">
                                    <el-input type="textarea" :rows="4" v-model="candidateForm.introduce" style="width: 100%;"></el-input>
                                </el-form-item>

                                <el-form-item label="备注" prop="remark">
                                    <el-input type="textarea" :rows="3" v-model="candidateForm.remark" style="width: 100%;"></el-input>
                                </el-form-item>

                            </el-col>
                            <div style="margin-bottom: 20px; text-align: right;">
                        <el-upload
                            action="#"
                            :auto-upload="false"
                            :show-file-list="false"
                            :on-change="handleJsonUpload"
                            accept=".json"
                        >
                            <el-button type="success" icon="el-icon-upload">上传JSON文件填充表单</el-button>
                        </el-upload>
                    </div>
                        </el-row>
                       
                        <el-form-item>
                            <el-button type="primary" @click="createCandidate">立即提交</el-button>
                            <el-button>取消</el-button>
                        </el-form-item>
                    </el-form>

                </div>

            </el-tab-pane>
        </el-tabs>

    </div>
</template>

<script>

module.exports = {
    data() {
        return {
            activeTab: "createCandidate",
            activeTitle: "",

            candidateForm: {
                jobId: "",
                realName: "",
                identityNum: "",
                sex: "",
                mobile: "",
                email: "",
                birthday: "",
                school: "",
                major: "",
                certificate: "",
                awards: "",
                experiment: "",
                introduce: "",
                remark: "",
            },
            jobNameList: [],

            rules: {
                jobId: [
                    { required: true, message: '请选择面试岗位', trigger: 'blur' },
                ],
                realName: [
                    { required: true, message: '姓名不能为空', trigger: 'blur' },
                ],
                identityNum: [
                    { required: true, message: '身份证号码不能为空', trigger: 'blur' },
                ],
                sex: [
                    { required: true, message: '性别不能为空', trigger: 'blur' },
                ],
                mobile: [
                    { required: true, message: '手机号不能为空', trigger: 'blur' },
                ],
                email: [
                    { required: true, message: '邮箱不能为空', trigger: 'blur' },
                ],
            },
        }
    },
    mounted() {
        var me = this;

        var candidateId = this.$route.query.candidateId;
        console.log("candidateId = " + candidateId);

        if (app.isNotEmpty(candidateId)) {
            var params = {
                candidateId: candidateId
            }

            me.activeTitle = "编辑面试者"

            this.getCandidate(candidateId);
        } else {
            me.activeTitle = "创建面试者"
        }

        this.initJobNameList();

    },
    methods: {
     handleJsonUpload(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const jsonData = JSON.parse(e.target.result);
                    this.fillFormWithJsonData(jsonData);
                    this.$message.success('JSON文件解析成功，表单已自动填充');
                } catch (error) {
                    console.error('JSON解析错误:', error);
                    this.$message.error('JSON文件格式不正确，请检查后重新上传');
                }
            };
            reader.readAsText(file.raw);
            
            // 清除上传文件列表，允许重复上传同一文件
            this.$refs.upload && this.$refs.upload.clearFiles();
        },
        
        // 使用JSON数据填充表单
        fillFormWithJsonData(jsonData) {
            // 映射JSON字段到表单字段
            const fieldMapping = {
                // 基本信息
                jobId: 'jobId',
                realName: 'realName',
                sex: 'sex',
                identityNum: 'identityNum',
                email: 'email',
                mobile: 'mobile',
                birthday: 'birthday',
                
                // 个人资质
                certificate: 'certificate',
                awards: 'awards',
                
                // 个人经历
                school: 'school',
                major: 'major',
                experiment: 'experiment',
                introduce: 'introduce',
                remark: 'remark'
            };
            
            // 遍历映射并填充表单
            Object.keys(fieldMapping).forEach(jsonKey => {
                const formKey = fieldMapping[jsonKey];
                if (jsonData[jsonKey] !== undefined && jsonData[jsonKey] !== null) {
                    this.candidateForm[formKey] = jsonData[jsonKey];
                }
            });
        },
        getCandidate(candidateId) {
            candidateApi.detail(candidateId).then(response => {
                // console.log(response);
                
                var candidate = response.data;
                candidate.sex = String(candidate.sex);

                console.log(candidate);

                this.candidateForm = candidate;
            });
        },

        createCandidate() {
            console.log(this.candidateForm);

            var candidateForm = this.candidateForm;

            var formName = "candidateForm";
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    this.$confirm('确认提交内容吗?', '提示', {
                        confirmButtonText: '确定',
                        cancelButtonText: '取消',
                        type: 'warning'
                    }).then(() => {
                        this.submitContent();
                    }).catch(() => {
                    });;
                } else {
                    console.log('提交错误!!!');
                    return false;
                }
            });
            
        },

        submitContent() {
            var bo = this.candidateForm;
            console.log(bo);

            candidateApi.createOrUpdate(bo).then(response => {
                console.log(response);

                this.$message({
                    showClose: true,
                    message: '面试者信息保存成功!',
                    type: 'success',
                    duration: 2000
                });

                this.clearForm();
            });

        },

        clearForm() {
            this.candidateForm = {
                jobId: "",
                realName: "",
                identityNum: "",
                sex: "",
                mobile: "",
                email: "",
                birthday: "",
                country: "",
                province: "",
                city: "",
                district: "",
                address: "",
                school: "",
                major: "",
                certificate: "",
                awards: "",
                experiment: "",
                introduce: "",
                remark: "",
            }
        },

        initJobNameList() {
            jobApi.nameList().then(response => {
                console.log(response);
                var jobNameList = response.data;
                this.jobNameList = jobNameList;
            });
        },

    },
}
</script>

<style>
.orderCreate-box {
    /* padding: 10px; */

    display: flex;
    flex-direction: column;
    justify-content: flex-start;

    /* border: solid 10px #e3e9ef; */

    font-size: 16px;
}

.orderCreate-box .table-wrapper {
    padding: 10px 10px 20px 10px;
}

.orderCreate-box .table-list {
    width: 100%;
    font-size: 15px;
}

.orderCreate-box .search-area {
    margin-bottom: 20px;

}

.form-group-title {
    margin: 15px 0 10px 0;
    color: #409EFF;
    font-size: 16px;
    font-weight: 500;
}

</style>