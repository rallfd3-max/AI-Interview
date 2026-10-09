<template>
	<view class="orderCreate-box">
		<!-- 标题 -->
		<view class="title">
			请确认信息并选择你要面试的岗位
		</view>

		<view class="table-wrapper">
			<form>
				<!-- 面试岗位选择 -->
				<view class="form-item">
					<text class="label">面试岗位</text>
					<picker v-model="selectedJobIndex" :range="jobList" :range-key="'jobName'" @change="onJobChange">
						<view class="picker">
							{{ getJobNameById(jobList[selectedJobIndex].jobId) }}
						</view>
					</picker>
				</view>

				<!-- 姓名 -->
				<view class="form-item">
					<text class="label">姓名</text>
					<text class="info">{{ candidateForm.realName }}</text>
				</view>

				<!-- 身份证号码 -->
				<view class="form-item">
					<text class="label">身份证号码</text>
					<text class="info">{{ candidateForm.identityNum }}</text>
				</view>

				<!-- 性别 -->
				<view class="form-item">
					<text class="label">性别</text>
					<text class="info">{{ sexOptions[candidateForm.sex] }}</text>
				</view>

				<!-- 手机号 -->
				<view class="form-item">
					<text class="label">手机号</text>
					<text class="info">{{ candidateForm.mobile }}</text>
				</view>

				<!-- 邮箱 -->
				<view class="form-item">
					<text class="label">邮箱</text>
					<text class="info">{{ candidateForm.email }}</text>
				</view>

				<!-- 毕业学校 -->
				<view class="form-item">
					<text class="label">毕业学校</text>
					<text class="info">{{ candidateForm.school || '-' }}</text>
				</view>

				<!-- 专业 -->
				<view class="form-item">
					<text class="label">专业</text>
					<text class="info">{{ candidateForm.major || '-' }}</text>
				</view>

				<!-- 出生日期 -->
				<view class="form-item">
					<text class="label">出生日期</text>
					<text class="info">{{ candidateForm.birthday }}</text>
				</view>

				<!-- 按钮 -->
				<view class="form-item">
					<button v-if="!isJobSelected" @click="submitEdit">确认提交</button>
					<button v-else @click="startInterview">开始面试</button>
				</view>
			</form>
		</view>
	</view>
</template>

<script>
	var app = getApp();
	export default {
		data() {
			return {
				cnt: true,
				candidateForm: {
					id:"",
					jobId: null, // 默认岗位ID
					realName: "",
					identityNum: "",
					sex: 2, // 默认性别为"保密"
					mobile: "",
					email: "",
					school: "", // 新增学校字段
					major: "", // 新增专业字段
					birthday: "",
				},
				jobList: [{
					jobName: "请选择要面试的岗位",
					jobId: null,
				}], // 默认岗位列表
				sexOptions: ["女", "男", "保密"], // 性别选项
				selectedJobIndex: 0, // 当前选中的岗位索引
				isJobSelected: false, // 是否已选择岗位
				candidateId: ''
			};
		},
		// onShow() {
		// 	// 恢复 candidateId
		// 	this.candidateId = this.candidateId || ' ';
		// 	if (this.candidateId ) {
		// 		this.initData();
		// 	}
		// },
		// mounted() {
		// 	this.initData(); 
		// },
		onLoad(options) {
			// console.log("从review过来的信息", options);
			// 从高到低优先级获取数据
			this.candidateId = options.candidateId;
			// console.log("从review过来的信息candidateId", options.candidateId);
			this.initData(); // 启动初始化

		},
		methods: {
			async initData() {
				const steps = {
					fetchUser: false,
					fetchJobs: false
				};

				try {
					steps.fetchUser = await this.fetchCandidateInfo(); //await
					steps.fetchJobs = await this.getJobList();

					if (!steps.fetchUser || !steps.fetchJobs) {
						throw new Error(`步骤未完成: ${JSON.stringify(steps)}`);
					}

					this.setJobIdIndex();
				} catch (e) {
					console.error('初始化序列失败:', steps, e);
				}
			},

			// 获取候选人信息
			fetchCandidateInfo() {
				return new Promise((resolve, reject) => {
					const candidateInfo = app.getUserInfoSession();
					// console.log("fetch从本地调取的数据", candidateInfo);
					const candidateId = this.candidateId || candidateInfo.candidateId;
					if (this.candidateId) {
						// console.log("fetch当中实际得到的为全局变量中的", candidateId);
					} else {
						// console.log("fetch当中实际得到的为本地存储的", candidateId);
					}
					// console.log("fetch当中实际得到的", candidateId);
					const serverUrl = getApp().globalData.serverUrl;
					uni.request({
						url: serverUrl + "/candidate/detail?candidateId=" + candidateId,
						success: (res) => {
							if (res.data.status === 200) {
								if (this.cnt) {
									res.data.data.jobId = null;
									this.cnt = false;
								}
								this.candidateForm = res.data.data;
								this.isJobSelected = !!this.candidateForm.jobId;
								// console.log("isJobSelected，form当中是否有jobId", this.isJobSelected);
								// console.log("fetch当中的从/candidate/detail得到的数据（后面的candidateform）;", res.data.data);

								this.setJobIdIndex();
								resolve(true); // 标记步骤完成
							} else {
								uni.showToast({
									title: "获取候选人信息失败",
									icon: "none"
								});
								resolve(false); // 标记步骤失败
							}
						},
						fail: (err) => {
							console.error("Error fetching candidate info:", err);
							reject(err); // 拒绝 Promise
						}
					});
				});
			},


			// 获取岗位列表
			getJobList() {
				return new Promise((resolve, reject) => {
					const serverUrl = getApp().globalData.serverUrl;

					uni.request({
						url: serverUrl + "/job/nameList",
						success: (res) => {
							if (res.data.status === 200) {
								this.jobList = [
									// { jobName: "请选择要面试的岗位", jobId: null },
									{
										jobName: "请选择要面试的岗位"
									},
									...res.data.data
								];
								// console.log("在getJobList函数中从后端获取的数据", res.data.data);
								this.setJobIdIndex();
								// console.log("在getJobList函数中设置的joblist", this.jobList);
								resolve(true); // 标记步骤完成
							} else {
								uni.showToast({
									title: "获取职位列表失败",
									icon: "none"
								});
								resolve(false); // 标记步骤失败
							}
						},
						fail: (err) => {
							console.error("Error fetching job list:", err);
							reject(err); // 拒绝 Promise
						}
					});
				});
			},
			// 设置岗位ID的索引
			setJobIdIndex() {
				if (this.candidateForm.jobId !== null) {
					// 根据 jobId 设置当前选中的岗位索引
					const selectedIndex = this.jobList.findIndex(
						(job) => job.jobId === this.candidateForm.jobId
					);
					// console.log("在setJobIdIndex函数中设置的岗位ID的索引", this.candidateForm.jobId)
					if (selectedIndex !== -1) {
						this.selectedJobIndex = selectedIndex; // 更新选中的索引
					}
				}
			},

			// 获取岗位名称
			getJobNameById(jobId) {
				if (jobId === null) return "请选择要面试的岗位"; // 如果没有jobId，返回默认值
				const job = this.jobList.find((item) => item.jobId === jobId);
				return job ? job.jobName : "请选择要面试的岗位"; // 返回岗位名称
			},

			// 处理岗位选择变化
			onJobChange(event) {
				const selectedIndex = event.detail.value; // 获取选中的索引
				const selectedJob = this.jobList[selectedIndex];
				if (selectedJob) {
					this.candidateForm.jobId = selectedJob.jobId; // 更新jobId
					this.selectedJobIndex = selectedIndex; // 同步更新selectedJobIndex
				};
				this.submitEdit();
			},

			// 提交编辑候选人信息
			submitEdit() {
				if (this.candidateForm.jobId === null) {
					uni.showToast({
						title: "请选择要面试的岗位",
						icon: "none",
					});
					return;
				}
				const selectedJobName = this.getJobNameById(this.candidateForm.jobId);

				uni.showModal({
					title: "确认提交",
					content: `您当前选择的面试岗位为 ${selectedJobName}，提交后不可修改，确认提交吗？`,
					success: (res) => {
						if (res.confirm) {
							const params = {
								...this.candidateForm
							};
							console.log("submitEdit提交的参数:", params);
							var serverUrl = getApp().globalData.serverUrl;

							uni.request({
								url: serverUrl + "/candidate/createOrUpdate",
								method: "POST",
								data: params,
								success: (res) => {
									if (res.data.status === 200) {
										uni.showToast({
											title: "信息更新成功",
											icon: "success",
										});
										this.fetchCandidateInfo();
									} else {
										uni.showToast({
											title: res.data.msg || "更新失败",
											icon: "none",
										});
									}
								},
								fail: (err) => {
									console.error("Error submitting candidate edit:", err);
									uni.showToast({
										title: "网络请求失败",
										icon: "none",
									});
								},
							});
						} else {
							uni.showToast({
								title: "提交已取消",
								icon: "none",
							});
						}
					},
				});
			},

			// 开始面试
			startInterview() {
				var me = this;
				var serverUrl = getApp().globalData.serverUrl;
				var candidateId = this.candidateId ||app.getUserInfoSession().candidateId;
				var jobId = this.candidateForm.jobId;
				const selectedJob = this.jobList[this.selectedJobIndex];

				// 检查是否选择了有效岗位
				if (!selectedJob || selectedJob.jobId === null) {
					uni.showToast({
						title: "请先选择要面试的岗位",
						icon: "none"
					});
					return;
				}

				// 正确获取jobName
				const jobName = selectedJob.jobName;
				// 检查是否已有面试记录
				uni.request({
					url: serverUrl + "/interviewRecord/check?candidateId=" + candidateId + "&jobName=" +
						encodeURIComponent(jobName),
					success: (res) => {
						console.log("面试记录检查结果:", res);
						if (res.data.status === 200 && res.data.data === true) {
							// 已有面试记录，跳转结果页
							uni.navigateTo({
								url: `/pages/me?jobId=${this.candidateForm.jobId}&candidateId=${this.candidateForm.id}&mobile=${this.candidateForm.mobile}` ,
								animationType: "slide-in-bottom",
							});
						} else {
							// 没有面试记录，正常进入面试
							console.log("无面试记录，响应数据:", res);
							console.log("岗位ID:", jobId);
							uni.navigateTo({
								url: "/pages/interviewer?jobName=" + encodeURIComponent(jobName) +
									"&jobId=" + jobId,
								animationType: "slide-in-bottom",
							});
						}
					},
					fail: (err) => {
						console.error("检查面试记录失败:", err);
						uni.showToast({
							title: "网络异常，请重试",
							icon: "none"
						});
					}
				});
			},
		},
	};
</script>

<style>
	@import url("jobselect.css");
</style>