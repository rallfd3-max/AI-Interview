<template>
	<view class="container">
		<view class="page-content">
			<!-- 面试信息展示区 -->
			<view v-if="!resultFetched" class="submit-box">
				<image src="../static/icons/submitted-1.png" class="icon-submit"></image>
				<text class="done-text">面试完毕，正在获取面试结果，请稍后！</text>

				<!-- 新增进度条 -->
				<view class="progress-container">
					<view class="progress-bar" :style="{width: progress + '%'}"></view>
				</view>
				<text class="progress-text">{{progress}}%</text>
			</view>

			<view v-else>
				<view class="score-title">面试总分</view>
				<!-- 面试信息展示区 -->
				<view class="interview-info">
					<view class="job-name">
						<text class="label">职位名称:</text>
						<text class="value">{{ jobName }}</text>
					</view>
					<view class="score">
						<text class="label">面试总分:</text>
						<text class="value">{{ totalScore }}</text>
					</view>
					<view class="offer-status">
						<text class="label">初试结果:</text>
						<text class="value" :class="offerStatus ? 'pass' : 'fail'">
							{{ offerStatus ? '通过' : '未通过' }}
						</text>
					</view>
				</view>

				<!-- 初试结果提示 -->
				<view class="interview-result">
					<text class="result-text">
						{{ offerStatus ? '恭喜您通过初试，请选择是否立即复试' : '很抱歉，您未能通过初试' }}
					</text>
				</view>
				<view v-if="offerStatus" class="action-buttons">
					<button class="action-button" @click="goToReview">参加复试</button>
					<button class="action-button secondary" @click="delayReview">暂时不复试</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	var app = getApp();
	export default {
		data() {
			return {
				API_BASE_URL: 'http://100.90.235.16:8000',//服务器ip
				candidateId: '',
				jobName: '',
				realName: '',
				mobile: '',
				jobId: '',
				totalScore: 0,
				qrcodeUrl: '', //二维码 
				offerStatus: '',
				resultFetched: false,
				progress: 0,
				progressInterval: null,
				pollingInterval: null, // 新增轮询定时器变量
				showConfirmDialog: false, // 新增标记是否显示确认对话框
				isReexamed: true
			};
		},
		mounted() {
			this.startProgress();
			this.startPolling();
			this.GetHistoryRecord();
		},
		onUnload() {
			this.clearAllIntervals();
		},
		beforeDestroy() {
			this.clearAllIntervals();
		},
		onLoad(options) {
			this.jobId = options.jobId;
			this.candidateId = options.candidateId;
			this.mobile = options.mobile;
			console.log("传来的jobId", this.jobId);
			console.log("传来的candidateId", this.candidateId);
			console.log("传来的mobile", this.mobile);

		},
		methods: {
			async GetHistoryRecord() {
				try {
					
					const url = `${this.API_BASE_URL}/history-message?id=${this.mobile}`;
					const [error, response] = await new Promise(resolve => {
						uni.request({
							url: url,
							method: 'GET', //查询数据
							success: (res) => resolve([null, res]), //初始化
							fail: (err) => resolve([err, null])
						});
					});

					if (error) throw error;
					
					// console.log("response", response.data)
					const isReexamed = JSON.parse(response.data)["flag"];
					console.log("me",isReexamed)
					this.isReexamed = isReexamed;
				} catch (error) {
					consol.log("me",error.message);
					uni.showToast({
						title: '退出失败: ' + (error.message || '网络错误'),
						icon: 'none'
					});
				}
			},

			// 清除所有定时器
			clearAllIntervals() {
				if (this.progressInterval) {
					clearInterval(this.progressInterval);
					this.progressInterval = null;
				}
				if (this.pollingInterval) {
					clearInterval(this.pollingInterval);
					this.pollingInterval = null;
				}
			},
			// 开始进度条动画
			startProgress() {
				// 清除之前的定时器（重要！）
				if (this.progressInterval) {
					clearInterval(this.progressInterval);
					this.progressInterval = null;
				}

				this.progressInterval = setInterval(() => {
					if (this.progress < 90 && !this.showConfirmDialog) {
						this.progress += 10;
					}
				}, 300);
			},
			// 开始轮询
			startPolling() {
				// 清除之前的轮询定时器
				if (this.pollingInterval) {
					clearInterval(this.pollingInterval);
					this.pollingInterval = null;
				}

				this.pollingInterval = setInterval(() => {
					if (!this.showConfirmDialog) {
						this.pollForInterviewResult();
					}
				}, 3000);
			},
			// 获取面试结果
			pollForInterviewResult() {
				// var candidateInfo = app.getUserInfoSession();
				// var candidateId = candidateInfo.candidateId;
				// this.candidateId = candidateId;
				// console.log("me中从本地调用的",candidateInfo);
				const candidateId = this.candidateId;
				var serverUrl = getApp().globalData.serverUrl;

				uni.request({
					url: serverUrl + "/interviewRecord/findById?candidateId=" + candidateId + "&jobId=" +
						this.jobId + "&realName=&mobile=&page=1&pageSize=10",
					success: (res) => {
						console.log("完整接口响应:", res);
						if (res.data.status === 200 && res.data.data.rows.length > 0 && !this
							.showConfirmDialog) {
							const data = res.data.data.rows[0];
							console.log("面试结果数据:", data);
							this.jobName = data.jobName;
							this.mobile = data.mobile;
							this.realName = data.realName;

							// 标记显示确认对话框
							this.showConfirmDialog = true;

							// 进度条加载到100%
							this.progress = 100;



							setTimeout(() => {
								uni.showModal({
									title: '提示',
									content: '面试结果已获取，是否立即查看？',
									success: (res) => {
										if (res.confirm) {
											this.totalScore = data.totalscore;
											this.offerStatus = data.offsta;
											this.qrcodeUrl = data.qrcodeUrl;
											this.resultFetched = true;
											uni.setStorageSync('interviewed_job_' +
												this.jobName, true);
											this.clearAllIntervals();

										} else {
											// 用户取消查看，重置状态继续轮询
											this.progress = 0;
											this.showConfirmDialog = false;

											// 重新开始进度条和轮询
											this.startProgress();
											this.startPolling();
										}
									},
									complete: () => {
										this.showConfirmDialog = false;
									}
								});
							}, 500);
						}
					},
					fail: (err) => {
						console.error("Error fetching interview result:", err);
					},
				});
			},

			goToReview() {
				const encodedName = encodeURIComponent(this.realName);
				const encodedJob = encodeURIComponent(this.jobName);
				const isReexamed = this.isReexamed;
				if (!isReexamed) {
					uni.navigateTo({
						url: `/pages/review?mobile=${this.mobile}&candidateName=${encodedName}&jobTitle=${encodedJob}&candidateId=${this.candidateId}&jobId=${this.jobId}`,
						animationType: "slide-in-bottom"
					});
				} else {
					uni.showToast({
						title: '您已参加过复试',
						icon: 'none',
						duration: 1500
					})

					// console.log("向review传递的jobId",this.jobId);
				}
			},
			delayReview() {
				uni.showToast({
					title: '您已选择暂时不复试，可稍后操作',
					icon: 'none'
				});
			}
		},
	};
</script>


<style>
	@import url("me.css");
</style>